"""Expand-and-Contract Database Migration Script for Day-4 Changed Requirements (Q6).
Migrates legacy pre-Day-4 SQLite schemas (without campus_code, policy_version, sync_status,
policies, or integration_outbox) to the Day-4 schema while preserving 100% of existing
bookings, tickets, and immutable audit history.
"""
import argparse
from pathlib import Path
import shutil
import sqlite3
import sys


def create_legacy_v1_database(db_path: str) -> None:
    """Create a representative pre-Day-4 legacy database and seed historical records."""
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        DROP TABLE IF EXISTS tickets;
        DROP TABLE IF EXISTS audit;
        DROP TABLE IF EXISTS bookings;
        DROP TABLE IF EXISTS policies;
        DROP TABLE IF EXISTS integration_outbox;

        CREATE TABLE tickets(
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            state TEXT NOT NULL,
            version INTEGER NOT NULL,
            notes TEXT,
            source TEXT,
            event_id TEXT,
            UNIQUE(source, event_id)
        );
        CREATE TABLE audit(
            id INTEGER PRIMARY KEY,
            ticket_id INTEGER,
            from_state TEXT,
            to_state TEXT,
            actor TEXT
        );
        CREATE TABLE bookings(
            id INTEGER PRIMARY KEY,
            facility TEXT,
            start_min INTEGER,
            end_min INTEGER,
            status TEXT
        );
        """
    )
    # Seed legacy bookings, tickets, and audit transitions
    conn.execute("INSERT INTO bookings(facility, start_min, end_min, status) VALUES ('Lab-204', 540, 660, 'Approved')")
    conn.execute("INSERT INTO bookings(facility, start_min, end_min, status) VALUES ('Seminar-102', 660, 780, 'Pending')")
    conn.execute("INSERT INTO bookings(facility, start_min, end_min, status) VALUES ('Auditorium-A', 800, 920, 'Approved')")

    conn.execute("INSERT INTO tickets(title, state, version, notes, source, event_id) VALUES ('Water leak in Lab-204 ceiling', 'Resolved', 4, 'Sealed pipe joint', 'sensor-1', 'evt-101')")
    conn.execute("INSERT INTO tickets(title, state, version, notes, source, event_id) VALUES ('Projector display fault in Seminar-102', 'In Progress', 3, NULL, 'manual', 'evt-102')")

    conn.executemany(
        "INSERT INTO audit(ticket_id, from_state, to_state, actor) VALUES (?,?,?,?)",
        [
            (1, "New", "Assigned", "manager"),
            (1, "Assigned", "In Progress", "technician"),
            (1, "In Progress", "Resolved", "technician"),
            (2, "New", "Assigned", "manager"),
            (2, "Assigned", "In Progress", "technician"),
        ],
    )
    conn.commit()
    conn.close()


def run_expand_and_contract_migration(db_path: str, simulate_failure: bool = False) -> dict:
    """Execute staged Expand -> Backfill -> Verify migration on db_path."""
    backup_path = f"{db_path}.pre_day4.bak"
    shutil.copy2(db_path, backup_path)

    conn = sqlite3.connect(db_path)
    pre_counts = {
        "bookings": conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
        "tickets": conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
        "audit": conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0],
    }

    try:
        # Phase 1: EXPAND (Add nullable/defaulted columns and new tables without breaking old queries)
        booking_cols = {r[1] for r in conn.execute("PRAGMA table_info(bookings)").fetchall()}
        for col, ddl in [
            ("requester", "TEXT DEFAULT 'faculty'"),
            ("campus_code", "TEXT DEFAULT 'MAIN_CAMPUS'"),
            ("policy_version", "TEXT DEFAULT 'v1'"),
            ("sync_status", "TEXT DEFAULT 'Synced'"),
            ("created_at", "TEXT DEFAULT '2026-11-18T00:00:00Z'"),
        ]:
            if col not in booking_cols:
                conn.execute(f"ALTER TABLE bookings ADD COLUMN {col} {ddl}")

        ticket_cols = {r[1] for r in conn.execute("PRAGMA table_info(tickets)").fetchall()}
        for col, ddl in [
            ("priority", "TEXT DEFAULT 'M2'"),
            ("category", "TEXT DEFAULT 'Facilities'"),
            ("campus_code", "TEXT DEFAULT 'MAIN_CAMPUS'"),
            ("policy_version", "TEXT DEFAULT 'v1'"),
            ("sync_status", "TEXT DEFAULT 'Synced'"),
            ("created_at", "TEXT DEFAULT '2026-11-18T00:00:00Z'"),
        ]:
            if col not in ticket_cols:
                conn.execute(f"ALTER TABLE tickets ADD COLUMN {col} {ddl}")

        audit_cols = {r[1] for r in conn.execute("PRAGMA table_info(audit)").fetchall()}
        if "created_at" not in audit_cols:
            conn.execute("ALTER TABLE audit ADD COLUMN created_at TEXT DEFAULT '2026-11-18T00:00:00Z'")

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS policies(
                campus_code TEXT PRIMARY KEY,
                policy_version TEXT NOT NULL,
                max_duration INTEGER NOT NULL,
                temp_limit REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS integration_outbox(
                id INTEGER PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                target_system TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'Pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                next_retry_at TEXT,
                remote_id TEXT,
                last_error TEXT
            );
            """
        )

        # Phase 2: BACKFILL legacy rows & seed campus-specific policies
        conn.execute(
            "INSERT OR REPLACE INTO policies(campus_code, policy_version, max_duration, temp_limit) VALUES ('MAIN_CAMPUS', 'v1', 180, 28.0)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO policies(campus_code, policy_version, max_duration, temp_limit) VALUES ('RESEARCH_ANNEX', 'v2', 240, 24.5)"
        )
        conn.execute("UPDATE bookings SET campus_code='MAIN_CAMPUS', policy_version='v1', sync_status='Synced' WHERE campus_code IS NULL")
        conn.execute("UPDATE tickets SET campus_code='MAIN_CAMPUS', policy_version='v1', sync_status='Synced' WHERE campus_code IS NULL")

        if simulate_failure:
            raise RuntimeError("Simulated mid-migration verification gate failure (row invariant abort)")

        # Phase 3: VERIFY row counts and audit invariants before committing release gate
        post_counts = {
            "bookings": conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
            "tickets": conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
            "audit": conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0],
            "policies": conn.execute("SELECT COUNT(*) FROM policies").fetchone()[0],
        }
        if (
            pre_counts["bookings"] != post_counts["bookings"]
            or pre_counts["tickets"] != post_counts["tickets"]
            or pre_counts["audit"] != post_counts["audit"]
        ):
            raise RuntimeError(f"Row count mismatch! Pre={pre_counts}, Post={post_counts}")

        conn.commit()
        conn.close()
        return {
            "status": "MIGRATION_SUCCESS",
            "pre_counts": pre_counts,
            "post_counts": post_counts,
            "backup_path": backup_path,
        }
    except Exception as exc:
        conn.close()
        # Automatic restore from verified pre-migration backup file
        shutil.copy2(backup_path, db_path)
        restored_conn = sqlite3.connect(db_path)
        restored_counts = {
            "bookings": restored_conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
            "tickets": restored_conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
            "audit": restored_conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0],
        }
        restored_conn.close()
        return {
            "status": "MIGRATION_ABORTED_AND_RESTORED",
            "error": str(exc),
            "pre_counts": pre_counts,
            "restored_counts": restored_counts,
            "backup_path": backup_path,
        }


def main():
    parser = argparse.ArgumentParser(description="Day-4 Expand-and-Contract Migration Runner")
    parser.add_argument("--db", default="./day4_migration_rehearsal.db", help="Target SQLite DB path")
    parser.add_argument("--seed-legacy", action="store_true", help="Create legacy v1 schema before migrating")
    parser.add_argument("--rehearse-failure", action="store_true", help="Rehearse controlled failure & backup restore first")
    args = parser.parse_args()

    db_path = str(Path(args.db).resolve())
    if args.seed_legacy or not Path(db_path).exists():
        create_legacy_v1_database(db_path)
        print(f"[SEED] Created pre-Day-4 legacy database at {db_path}")

    if args.rehearse_failure:
        fail_res = run_expand_and_contract_migration(db_path, simulate_failure=True)
        print(f"[REHEARSAL-FAIL-GATE] Status: {fail_res['status']} | Reason: {fail_res['error']}")
        print(f"[REHEARSAL-RESTORE] Pre-counts: {fail_res['pre_counts']} == Restored-counts: {fail_res['restored_counts']}")
        if fail_res["pre_counts"] != fail_res["restored_counts"]:
            sys.exit(1)

    res = run_expand_and_contract_migration(db_path, simulate_failure=False)
    print(f"[MIGRATION-EXPAND-CONTRACT] Status: {res['status']}")
    print(f"[MIGRATION-VERIFY] Pre-counts:  {res['pre_counts']}")
    print(f"[MIGRATION-VERIFY] Post-counts: {res['post_counts']}")
    if res["status"] != "MIGRATION_SUCCESS":
        sys.exit(1)


if __name__ == "__main__":
    main()
