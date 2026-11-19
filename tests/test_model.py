"""Automated Unit, Integration, and Regression Test Suite (Q2 & Q3).
Includes the 14 baseline checks from the reference appendix (U1-U6, I1-I4, R1-R4)
plus expanded boundary, SLA equality, FastAPI HTTP, and dependency outage checks (U7-U10, I5-I6, R5).
"""
from datetime import datetime, timedelta, timezone
import os
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.auth import create_signed_token
from app.main import app, set_store
import campus_model as m


# ---- Unit checks (U1 - U10) ----
def test_U1_high_high_is_M1():
    assert m.priority("High", "High") == "M1"


def test_U2_low_low_is_M4():
    assert m.priority("Low", "Low") == "M4"


def test_U3_impact_out_of_range():
    with pytest.raises(ValueError):
        m.priority("Critical", "High")


def test_U4_water_leak_is_facilities():
    assert m.classify("Water leak from lab ceiling") == "Facilities"


def test_U5_equal_evidence_manual():
    assert m.classify("Leak and projector fault") == "Manual Review"


def test_U6_temperature_threshold():
    assert (m.breached(28.0), m.breached(28.01)) == (False, True)


def test_U7_temperature_below_threshold_boundary():
    assert m.breached(27.99) is False


def test_U8_booking_duration_boundaries():
    assert m.valid_duration(0) is False
    assert m.valid_duration(179) is True
    assert m.valid_duration(180) is True
    assert m.valid_duration(181) is False


def test_U9_sla_deadline_and_equality_boundary():
    created = datetime(2026, 11, 18, 8, 0, 0, tzinfo=timezone.utc)
    deadline = m.sla_deadline(created, "M1")
    assert deadline == datetime(2026, 11, 18, 9, 0, 0, tzinfo=timezone.utc)
    # 1 second before deadline -> on-time (False)
    assert m.is_sla_overdue(deadline - timedelta(seconds=1), deadline) is False
    # Exact equality (0s) -> on-time (False) per explicit SLA equality rule
    assert m.is_sla_overdue(deadline, deadline) is False
    # 1 second after deadline -> overdue (True)
    assert m.is_sla_overdue(deadline + timedelta(seconds=1), deadline) is True


def test_U10_priority_matrix_all_nine_cells():
    expected = {
        ("High", "High"): "M1",
        ("High", "Medium"): "M2",
        ("High", "Low"): "M3",
        ("Medium", "High"): "M2",
        ("Medium", "Medium"): "M3",
        ("Medium", "Low"): "M4",
        ("Low", "High"): "M3",
        ("Low", "Medium"): "M4",
        ("Low", "Low"): "M4",
    }
    for (imp, urg), prio in expected.items():
        assert m.priority(imp, urg) == prio


# ---- Integration checks (real SQLite database & HTTP adapter interactions, I1 - I6) ----
def test_I1_commands_persist_and_audit(tmp_path):
    p = str(tmp_path / "campus.db")
    s = m.Store(p)
    t = s.create_ticket("AC compressor tripping in Lab 204")
    v = 1
    for target, notes in [
        ("Assigned", None),
        ("In Progress", None),
        ("Resolved", "Reset breaker"),
        ("Closed", None),
    ]:
        v = s.transition(t, target, v, "technician", notes)
    s.db.close()
    s2 = m.Store(p)  # close and reopen file database
    assert s2.state(t) == ("Closed", 5) and s2.audit_count(t) == 4
    s2.db.close()


def test_I2_repeated_event_one_ticket():
    s = m.Store()
    ids = {s.create_ticket("Temp high", "sensor-7", "evt-1") for _ in range(5)}
    assert len(ids) == 1 and s.count() == 1


def test_I3_student_cannot_approve_booking():
    s = m.Store()
    b = s.request_booking("Lab-204", 600, 720)
    with pytest.raises(PermissionError):
        s.approve_booking(b, "student")
    assert s.booking_status(b) == "Pending"


def test_I4_overlap_rejected_adjacent_allowed():
    s = m.Store()
    s.request_booking("Lab-204", 600, 720)
    with pytest.raises(RuntimeError):
        s.request_booking("Lab-204", 700, 800)
    s.request_booking("Lab-204", 720, 800)  # back-to-back is allowed
    assert s.count("bookings") == 2


def test_I5_fastapi_end_to_end_booking_ticket_audit_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("EXTERNAL_SYNC_FAIL", "false")
    store = m.Store(str(tmp_path / "api_e2e.db"))
    set_store(store)
    client = TestClient(app)

    faculty_token = create_signed_token("prof_kumar", "faculty")
    approver_token = create_signed_token("dean_rao", "approver")
    tech_token = create_signed_token("tech_anand", "technician")

    # Create booking
    r_book = client.post(
        "/api/v1/bookings",
        json={"facility": "Lab-204", "start_min": 540, "end_min": 660},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert r_book.status_code == 201
    bid = r_book.json()["id"]

    # Approve booking
    r_app = client.post(
        f"/api/v1/bookings/{bid}/approve",
        json={"notes": "Approved for robotics lab"},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert r_app.status_code == 200
    assert r_app.json()["status"] == "Approved"

    # Sensor breach creates ticket
    r_sens = client.post(
        "/api/v1/sensors/events",
        json={
            "source": "sensor-hvac-204",
            "event_id": "evt-900",
            "facility": "Lab-204",
            "temperature": 29.4,
        },
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r_sens.status_code == 200
    tid = r_sens.json()["ticket_id"]

    # Transition ticket New -> Assigned -> In Progress -> Resolved -> Closed
    for idx, (target, notes) in enumerate(
        [
            ("Assigned", None),
            ("In Progress", None),
            ("Resolved", "Replaced compressor relay"),
            ("Closed", None),
        ],
        start=1,
    ):
        r_tr = client.post(
            f"/api/v1/tickets/{tid}/transition",
            json={"target_state": target, "expected_version": idx, "notes": notes},
            headers={"Authorization": f"Bearer {tech_token}"},
        )
        assert r_tr.status_code == 200

    r_aud = client.get(
        f"/api/v1/tickets/{tid}/audit",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r_aud.status_code == 200
    assert r_aud.json()["audit_count"] == 4
    store.db.close()


def test_I6_external_dependency_outage_preserves_local_pending(tmp_path, monkeypatch):
    monkeypatch.setenv("EXTERNAL_SYNC_FAIL", "true")
    store = m.Store(str(tmp_path / "outage.db"))
    set_store(store)
    client = TestClient(app)
    token = create_signed_token("faculty_1", "faculty")

    res = client.post(
        "/api/v1/bookings",
        json={"facility": "Seminar-101", "start_min": 600, "end_min": 720},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "Pending"
    assert body["sync_status"] == "Pending"  # Never falsely marked Synced during outage
    store.db.close()


# ---- Regression checks (previously correct behaviour, R1 - R5) ----
def test_R1_high_medium_is_M2():
    assert m.priority("High", "Medium") == "M2"


def test_R2_unknown_terms_manual():
    assert m.classify("strange noise somewhere") == "Manual Review"


def test_R3_resolve_without_notes_rejected():
    s = m.Store()
    t = s.create_ticket("Door lock jammed")
    s.transition(t, "Assigned", 1, "technician")
    s.transition(t, "In Progress", 2, "technician")
    with pytest.raises(ValueError):
        s.transition(t, "Resolved", 3, "technician", "   ")
    assert s.state(t)[0] == "In Progress"


def test_R4_stale_version_rejected():
    s = m.Store()
    t = s.create_ticket("Display flicker")
    s.transition(t, "Assigned", 1, "technician")
    with pytest.raises(RuntimeError):
        s.transition(t, "In Progress", 1, "technician")
    assert s.state(t) == ("Assigned", 2)


def test_R5_missing_ticket_title_rejected():
    s = m.Store()
    with pytest.raises(ValueError):
        s.create_ticket("   ")
    assert s.count("tickets") == 0
