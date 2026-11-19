"""Post-Deployment End-to-End Smoke Verification Script.
Waits for /ready, authenticates via HMAC Bearer tokens, executes a full
create-booking -> approve-booking -> sensor-event -> ticket-transition -> audit-verify
journey, and verifies student RBAC rejection (403 Forbidden). Exits non-zero on any failure.
"""
import argparse
import os
import sys
import time

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.auth import create_signed_token


def run_smoke_journey(base_url: str, timeout_sec: int = 30) -> None:
    print(f"[SMOKE 1/6] Polling readiness gate at {base_url}/ready ...")
    deadline = time.time() + timeout_sec
    ready_ok = False
    last_err = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/ready", timeout=3.0)
            if r.status_code == 200 and r.json().get("status") == "ready":
                ready_ok = True
                print(f"  -> /ready PASSED: {r.json()}")
                break
            last_err = f"HTTP {r.status_code}: {r.text}"
        except Exception as exc:
            last_err = str(exc)
        time.sleep(1.0)

    if not ready_ok:
        print(f"[SMOKE FAIL] Service failed readiness check within {timeout_sec}s: {last_err}")
        sys.exit(1)

    faculty_token = create_signed_token("smoke_faculty", "faculty")
    approver_token = create_signed_token("smoke_approver", "approver")
    tech_token = create_signed_token("smoke_technician", "technician")
    student_token = create_signed_token("smoke_student", "student")

    print("[SMOKE 2/6] Creating facility booking via /api/v1/bookings ...")
    r_book = httpx.post(
        f"{base_url}/api/v1/bookings",
        json={"facility": "Lab-204", "start_min": 600, "end_min": 720},
        headers={"Authorization": f"Bearer {faculty_token}"},
        timeout=5.0,
    )
    if r_book.status_code != 201:
        print(f"[SMOKE FAIL] Booking creation failed: {r_book.status_code} {r_book.text}")
        sys.exit(1)
    bid = r_book.json()["id"]
    print(f"  -> Booking #{bid} created with status={r_book.json()['status']}")

    print("[SMOKE 3/6] Verifying student RBAC rejection (403 Forbidden) even with spoofed role payload ...")
    r_spoof = httpx.post(
        f"{base_url}/api/v1/bookings/{bid}/approve",
        json={"role": "approver", "notes": "Spoof attempt"},
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=5.0,
    )
    if r_spoof.status_code != 403:
        print(f"[SMOKE FAIL] Expected 403 for student approval attempt, got {r_spoof.status_code}")
        sys.exit(1)
    print(f"  -> Student role spoofing rejected with HTTP {r_spoof.status_code} Forbidden")

    print("[SMOKE 4/6] Approving booking with authorized approver token ...")
    r_app = httpx.post(
        f"{base_url}/api/v1/bookings/{bid}/approve",
        json={"notes": "Approved during post-deploy smoke check"},
        headers={"Authorization": f"Bearer {approver_token}"},
        timeout=5.0,
    )
    if r_app.status_code != 200 or r_app.json().get("status") != "Approved":
        print(f"[SMOKE FAIL] Booking approval failed: {r_app.status_code} {r_app.text}")
        sys.exit(1)
    print(f"  -> Booking #{bid} approved by {r_app.json()['approved_by']}")

    print("[SMOKE 5/6] Submitting sensor breach event (29.2C > 28.0C) and verifying idempotency ...")
    r_sens1 = httpx.post(
        f"{base_url}/api/v1/sensors/events",
        json={
            "source": "smoke-sensor-204",
            "event_id": f"smoke-evt-{bid}",
            "facility": "Lab-204",
            "temperature": 29.2,
            "impact": "High",
            "urgency": "High",
        },
        headers={"Authorization": f"Bearer {tech_token}"},
        timeout=5.0,
    )
    r_sens2 = httpx.post(
        f"{base_url}/api/v1/sensors/events",
        json={
            "source": "smoke-sensor-204",
            "event_id": f"smoke-evt-{bid}",
            "facility": "Lab-204",
            "temperature": 29.2,
            "impact": "High",
            "urgency": "High",
        },
        headers={"Authorization": f"Bearer {tech_token}"},
        timeout=5.0,
    )
    if r_sens1.status_code != 200 or r_sens1.json()["ticket_id"] != r_sens2.json()["ticket_id"]:
        print("[SMOKE FAIL] Sensor event ingestion or idempotency check failed")
        sys.exit(1)
    tid = r_sens1.json()["ticket_id"]
    print(f"  -> Idempotent Ticket #{tid} verified (priority={r_sens1.json()['priority']})")

    print("[SMOKE 6/6] Transitioning Ticket through lifecycle and verifying immutable audit log ...")
    transitions = [
        ("Assigned", 1, None),
        ("In Progress", 2, None),
        ("Resolved", 3, "Replaced faulty HVAC relay during smoke verification"),
        ("Closed", 4, None),
    ]
    for target, ver, notes in transitions:
        r_tr = httpx.post(
            f"{base_url}/api/v1/tickets/{tid}/transition",
            json={"target_state": target, "expected_version": ver, "notes": notes},
            headers={"Authorization": f"Bearer {tech_token}"},
            timeout=5.0,
        )
        if r_tr.status_code != 200:
            print(f"[SMOKE FAIL] Ticket transition to {target} failed: {r_tr.text}")
            sys.exit(1)

    r_audit = httpx.get(
        f"{base_url}/api/v1/tickets/{tid}/audit",
        headers={"Authorization": f"Bearer {tech_token}"},
        timeout=5.0,
    )
    if r_audit.status_code != 200 or r_audit.json().get("audit_count") != 4:
        print(f"[SMOKE FAIL] Expected 4 audit records, got {r_audit.text}")
        sys.exit(1)
    print(f"  -> Ticket #{tid} reached Closed state (version=5) with 4 immutable audit records.")
    print("[SMOKE PASS] All post-deployment smoke gates succeeded!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    run_smoke_journey(args.base_url)
