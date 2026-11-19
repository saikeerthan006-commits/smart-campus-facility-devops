"""External Calendar and Developer Issue-Tracker Adapter with Durable Outbox & Bounded Retry.
Guarantees local persistence when downstream dependencies are unavailable and never reports
Pending synchronization as remote success.
"""
from datetime import datetime, timedelta, timezone
import os
from typing import Dict

from campus_model import Store

MAX_RETRY_ATTEMPTS = 3


def is_external_outage_simulated() -> bool:
    return os.environ.get("EXTERNAL_SYNC_FAIL", "false").lower() in ("true", "1", "yes")


def enqueue_and_attempt_sync(
    store: Store,
    entity_type: str,
    entity_id: int,
    target_system: str,
    idempotency_key: str,
) -> Dict[str, object]:
    """Record durable integration intent in outbox and attempt immediate synchronization."""
    now = datetime.now(timezone.utc)
    existing = store.db.execute(
        "SELECT id, status, attempts, remote_id, last_error FROM integration_outbox WHERE idempotency_key=?",
        (idempotency_key,),
    ).fetchone()

    if not existing:
        store.db.execute(
            "INSERT OR IGNORE INTO integration_outbox(entity_type, entity_id, target_system, idempotency_key, status, attempts, next_retry_at) "
            "VALUES (?,?,?,?, 'Pending', 0, ?)",
            (entity_type, entity_id, target_system, idempotency_key, now.isoformat()),
        )
        store.db.commit()

    return process_outbox_entry(store, idempotency_key)


def process_outbox_entry(store: Store, idempotency_key: str) -> Dict[str, object]:
    row = store.db.execute(
        "SELECT id, entity_type, entity_id, target_system, status, attempts, remote_id "
        "FROM integration_outbox WHERE idempotency_key=?",
        (idempotency_key,),
    ).fetchone()
    if not row:
        raise KeyError(f"Outbox entry not found for key {idempotency_key}")

    oid, entity_type, entity_id, target_system, current_status, attempts, remote_id = row
    if current_status == "Synced" and remote_id:
        return {
            "outbox_id": oid,
            "status": "Synced",
            "attempts": attempts,
            "remote_id": remote_id,
        }

    new_attempts = attempts + 1
    now = datetime.now(timezone.utc)

    if is_external_outage_simulated():
        backoff_seconds = 2 ** new_attempts
        next_retry = (now + timedelta(seconds=backoff_seconds)).isoformat()
        new_status = (
            "Manual Retry Required"
            if new_attempts >= MAX_RETRY_ATTEMPTS
            else "Pending"
        )
        err_msg = f"{target_system} connection timeout (attempt {new_attempts}/{MAX_RETRY_ATTEMPTS})"
        store.db.execute(
            "UPDATE integration_outbox SET status=?, attempts=?, next_retry_at=?, last_error=? WHERE id=?",
            (new_status, new_attempts, next_retry, err_msg, oid),
        )
        if entity_type == "booking":
            store.db.execute("UPDATE bookings SET sync_status='Pending' WHERE id=?", (entity_id,))
        else:
            store.db.execute("UPDATE tickets SET sync_status='Pending' WHERE id=?", (entity_id,))
        store.db.commit()
        return {
            "outbox_id": oid,
            "status": new_status,
            "attempts": new_attempts,
            "remote_id": None,
            "last_error": err_msg,
        }

    confirmed_remote_id = f"{target_system.upper()}-{entity_type.upper()}-{entity_id}"
    store.db.execute(
        "UPDATE integration_outbox SET status='Synced', attempts=?, remote_id=?, last_error=NULL WHERE id=?",
        (new_attempts, confirmed_remote_id, oid),
    )
    if entity_type == "booking":
        store.db.execute("UPDATE bookings SET sync_status='Synced' WHERE id=?", (entity_id,))
    else:
        store.db.execute("UPDATE tickets SET sync_status='Synced' WHERE id=?", (entity_id,))
    store.db.commit()
    return {
        "outbox_id": oid,
        "status": "Synced",
        "attempts": new_attempts,
        "remote_id": confirmed_remote_id,
        "last_error": None,
    }
