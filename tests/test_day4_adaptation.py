"""Day-4 Changed Release Adaptation Test Suite (Q6).
Validates campus-specific versioned policies (MAIN_CAMPUS v1 vs RESEARCH_ANNEX v2),
backward-compatible /api/v1/bookings adapter + /api/v2/bookings endpoint,
expand-and-contract migration with zero data loss, controlled migration failure restore,
and durable outbox bounded retry during intermittent calendar/issue-tracker outages.
"""
import importlib.util
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.auth import create_signed_token
from app.main import app, set_store
import campus_model as m

MIGRATION_PATH = Path(__file__).resolve().parent.parent / "migrations" / "002_campus_policies_and_outbox.py"
spec = importlib.util.spec_from_file_location("migration_002", MIGRATION_PATH)
migration_002 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_002)


def test_day4_01_campus_specific_duration_and_sensor_thresholds():
    # MAIN_CAMPUS (v1): max_duration=180, temp_limit=28.0
    assert m.valid_duration(180, "MAIN_CAMPUS") is True
    assert m.valid_duration(181, "MAIN_CAMPUS") is False
    assert m.breached(28.0, "MAIN_CAMPUS") is False
    assert m.breached(28.01, "MAIN_CAMPUS") is True

    # RESEARCH_ANNEX (v2): max_duration=240, temp_limit=24.5
    assert m.valid_duration(210, "RESEARCH_ANNEX") is True
    assert m.valid_duration(240, "RESEARCH_ANNEX") is True
    assert m.valid_duration(241, "RESEARCH_ANNEX") is False
    assert m.breached(24.50, "RESEARCH_ANNEX") is False
    assert m.breached(24.51, "RESEARCH_ANNEX") is True


def test_day4_02_expand_and_contract_migration_preserves_legacy_records(tmp_path):
    db_file = str(tmp_path / "legacy_campus.db")
    migration_002.create_legacy_v1_database(db_file)

    # First rehearse controlled migration failure and verify automatic backup restore
    fail_res = migration_002.run_expand_and_contract_migration(db_file, simulate_failure=True)
    assert fail_res["status"] == "MIGRATION_ABORTED_AND_RESTORED"
    assert fail_res["pre_counts"] == fail_res["restored_counts"] == {"bookings": 3, "tickets": 2, "audit": 5}

    # Now execute full expand-and-contract migration
    ok_res = migration_002.run_expand_and_contract_migration(db_file, simulate_failure=False)
    assert ok_res["status"] == "MIGRATION_SUCCESS"
    assert ok_res["post_counts"]["bookings"] == 3
    assert ok_res["post_counts"]["tickets"] == 2
    assert ok_res["post_counts"]["audit"] == 5
    assert ok_res["post_counts"]["policies"] == 2

    # Open migrated DB with application Store and verify legacy records retain v1 policy
    store = m.Store(db_file)
    set_store(store)
    client = TestClient(app)
    token = create_signed_token("faculty_legacy", "faculty")

    r_v1 = client.get("/api/v1/bookings", headers={"Authorization": f"Bearer {token}"})
    assert r_v1.status_code == 200
    items = r_v1.json()["items"]
    assert len(items) == 3
    assert all(b["campus_code"] == "MAIN_CAMPUS" and b["policy_version"] == "v1" for b in items)
    store.db.close()


def test_day4_03_v1_compatibility_and_v2_campus_policy_api(tmp_path, monkeypatch):
    monkeypatch.setenv("EXTERNAL_SYNC_FAIL", "false")
    store = m.Store(str(tmp_path / "v1_v2_compat.db"))
    set_store(store)
    client = TestClient(app)
    token = create_signed_token("dr_mehta", "faculty")

    # Legacy v1 booking without campus_code defaults to MAIN_CAMPUS (v1) and rejects 200-min duration
    r_v1_reject = client.post(
        "/api/v1/bookings",
        json={"facility": "Main-Hall", "start_min": 600, "end_min": 800},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_v1_reject.status_code == 400

    # Revised v2 booking for RESEARCH_ANNEX accepts 200-min duration under policy v2 (max 240m)
    r_v2_ok = client.post(
        "/api/v2/bookings",
        json={
            "facility": "Cryo-Annex-01",
            "start_min": 600,
            "end_min": 800,
            "campus_code": "RESEARCH_ANNEX",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_v2_ok.status_code == 201
    body = r_v2_ok.json()
    assert body["campus_code"] == "RESEARCH_ANNEX"
    assert body["policy_version"] == "v2"
    assert body["duration_min"] == 200
    assert body["sync_status"] == "Synced"
    store.db.close()


def test_day4_04_durable_outbox_bounded_retry_and_recovery(tmp_path, monkeypatch):
    """During external outage, local ticket is preserved as Pending and escalates to Manual Retry Required after 3 failed attempts."""
    monkeypatch.setenv("EXTERNAL_SYNC_FAIL", "true")
    store = m.Store(str(tmp_path / "outbox_retry.db"))
    set_store(store)
    client = TestClient(app)
    tech_token = create_signed_token("tech_ops", "technician")

    # Sensor event at 25.0C in RESEARCH_ANNEX breaches v2 threshold (24.5C)
    r_sens = client.post(
        "/api/v1/sensors/events",
        json={
            "source": "cryo-sensor-1",
            "event_id": "evt-500",
            "facility": "Cryo-Annex-01",
            "temperature": 25.0,
            "campus_code": "RESEARCH_ANNEX",
        },
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r_sens.status_code == 200
    data = r_sens.json()
    assert data["breached"] is True
    assert data["policy_version"] == "v2"
    assert data["sync_status"] == "Pending"  # Never falsely shown as Synced

    idem_key = "issue-sensor-cryo-sensor-1-evt-500"
    # Attempt 2 (still failing)
    r_retry2 = client.post(
        f"/api/v1/outbox/{idem_key}/retry",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r_retry2.json()["status"] == "Pending"
    assert r_retry2.json()["attempts"] == 2

    # Attempt 3 (reaches max_attempts=3 -> escalates to Manual Retry Required)
    r_retry3 = client.post(
        f"/api/v1/outbox/{idem_key}/retry",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r_retry3.json()["status"] == "Manual Retry Required"
    assert r_retry3.json()["attempts"] == 3

    # External service recovers -> operator retry succeeds and confirms remote ID
    monkeypatch.setenv("EXTERNAL_SYNC_FAIL", "false")
    r_recover = client.post(
        f"/api/v1/outbox/{idem_key}/retry",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r_recover.json()["status"] == "Synced"
    assert r_recover.json()["remote_id"] == f"ISSUE-TRACKER-TICKET-{data['ticket_id']}"
    store.db.close()


def test_day4_05_dashboard_health_ready_and_outbox_endpoints(tmp_path, monkeypatch):
    monkeypatch.setenv("EXTERNAL_SYNC_FAIL", "false")
    monkeypatch.setenv("SIMULATE_BROKEN_RELEASE", "false")
    store = m.Store(str(tmp_path / "ui_endpoints.db"))
    set_store(store)
    client = TestClient(app)
    tech_token = create_signed_token("tech_lead", "technician")

    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    assert client.get("/").status_code == 200
    assert client.get("/api/v2/bookings", headers={"Authorization": f"Bearer {tech_token}"}).status_code == 200
    assert client.get(
        "/api/v2/bookings?campus_code=MAIN_CAMPUS",
        headers={"Authorization": f"Bearer {tech_token}"},
    ).status_code == 200
    assert client.get("/api/v1/outbox", headers={"Authorization": f"Bearer {tech_token}"}).status_code == 200
    assert client.get("/api/v1/facilities/restricted", headers={"Authorization": f"Bearer {tech_token}"}).status_code == 200
    store.db.close()

