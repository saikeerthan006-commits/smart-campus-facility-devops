"""Direct API Security, RBAC Enforcement, and Anti-Spoofing Validation (Q5)."""
import os
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.auth import create_signed_token
from app.main import app, set_store
import campus_model as m


@pytest.fixture
def isolated_client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "test-security-hmac-key-2026")
    monkeypatch.setenv("EXTERNAL_SYNC_FAIL", "false")
    store = m.Store(str(tmp_path / "security_test.db"))
    set_store(store)
    yield TestClient(app), store
    store.db.close()


def test_sec_01_student_spoofing_approver_in_json_body_rejected(isolated_client):
    """Student token claiming 'role': 'approver' in request body receives 403 and DB is unchanged."""
    client, store = isolated_client
    faculty_token = create_signed_token("faculty_user", "faculty")
    student_token = create_signed_token("student_rahul", "student")

    r_create = client.post(
        "/api/v1/bookings",
        json={"facility": "Lab-204", "start_min": 600, "end_min": 720},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert r_create.status_code == 201
    bid = r_create.json()["id"]

    # Student attempts direct API approval with spoofed role in JSON payload
    r_spoof = client.post(
        f"/api/v1/bookings/{bid}/approve",
        json={"role": "approver", "notes": "Spoofed self-approval attempt"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert r_spoof.status_code == 403
    assert store.booking_status(bid) == "Pending"


def test_sec_02_student_denied_restricted_facilities_and_tickets(isolated_client):
    client, store = isolated_client
    student_token = create_signed_token("student_rahul", "student")
    tech_token = create_signed_token("tech_1", "technician")

    # Create a ticket as technician
    r_t = client.post(
        "/api/v1/tickets",
        json={"title": "Ceiling leak in restricted lab", "impact": "High", "urgency": "High"},
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    tid = r_t.json()["id"]

    # Student attempts to read restricted facilities, ticket list, ticket audit, and transition ticket
    assert client.get(
        "/api/v1/facilities/restricted",
        headers={"Authorization": f"Bearer {student_token}"},
    ).status_code == 403

    assert client.get(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
    ).status_code == 403

    assert client.get(
        f"/api/v1/tickets/{tid}/audit",
        headers={"Authorization": f"Bearer {student_token}"},
    ).status_code == 403

    r_tr = client.post(
        f"/api/v1/tickets/{tid}/transition",
        json={"target_state": "Assigned", "expected_version": 1, "role": "technician"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert r_tr.status_code == 403
    assert store.state(tid) == ("New", 1)
    assert store.audit_count(tid) == 0


def test_sec_03_all_six_roles_permission_matrix(isolated_client):
    """Verify exact RBAC matrix across all 6 platform roles."""
    client, store = isolated_client
    roles = ["admin", "manager", "technician", "approver", "faculty", "student"]
    tokens = {r: create_signed_token(f"user_{r}", r) for r in roles}

    for idx, r in enumerate(roles):
        bid = store.request_booking("Lab-204", 100 + idx * 60, 150 + idx * 60)
        resp = client.post(
            f"/api/v1/bookings/{bid}/approve",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {tokens[r]}"},
        )
        if r in ("admin", "manager", "approver"):
            assert resp.status_code == 200
            assert store.booking_status(bid) == "Approved"
        else:
            assert resp.status_code == 403
            assert store.booking_status(bid) == "Pending"


def test_sec_04_tampered_or_missing_token_rejected(isolated_client):
    client, _ = isolated_client
    assert client.get("/api/v1/facilities/restricted").status_code == 401
    valid_token = create_signed_token("student_1", "student")
    tampered_token = valid_token[:-4] + "0000"
    assert client.get(
        "/api/v1/facilities/restricted",
        headers={"Authorization": f"Bearer {tampered_token}"},
    ).status_code == 401
