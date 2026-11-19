"""Compact test model and core domain rules of the Smart Campus Facility Platform (Python + SQLite).
Note: Classification uses deterministic keyword matching rules (not trained machine learning).
"""
from datetime import datetime, timedelta, timezone
import sqlite3
import threading

MATRIX = {
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

KEYWORDS = {
    "Facilities": ["leak", "flood", "ceiling", "door", "lock"],
    "HVAC": ["ac", "compressor", "temperature", "cooling"],
    "AV-Network": ["projector", "display", "wifi", "network"],
}

MAX_MINUTES = 180
TEMP_LIMIT = 28.0

SLA_HOURS = {
    "M1": 1,
    "M2": 4,
    "M3": 24,
    "M4": 72,
}

TRANSITIONS = {
    "New": ["Assigned"],
    "Assigned": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed"],
    "Closed": [],
}

ROLES = {"admin", "manager", "technician", "approver", "faculty", "student"}
STAFF = {"technician", "manager", "admin"}
APPROVERS = {"approver", "manager", "admin"}

CAMPUS_POLICIES = {
    "MAIN_CAMPUS": {
        "campus_code": "MAIN_CAMPUS",
        "policy_version": "v1",
        "max_duration": 180,
        "temp_limit": 28.0,
    },
    "RESEARCH_ANNEX": {
        "campus_code": "RESEARCH_ANNEX",
        "policy_version": "v2",
        "max_duration": 240,
        "temp_limit": 24.5,
    },
}


def priority(impact: str, urgency: str) -> str:
    if (impact, urgency) not in MATRIX:
        raise ValueError("invalid matrix input")
    return MATRIX[impact, urgency]


def classify(text: str) -> str:
    """Deterministic keyword-rule classifier. Ties or zero matches route to Manual Review."""
    if not text or not text.strip():
        return "Manual Review"
    words = text.lower().replace(",", " ").replace(".", " ").split()
    scores = {c: sum(1 for w in words if w in kws) for c, kws in KEYWORDS.items()}
    best = max(scores.values())
    top = [c for c, s in scores.items() if s == best]
    if best == 0 or len(top) != 1:
        return "Manual Review"
    return top[0]


def breached(value: float, campus_code: str = "MAIN_CAMPUS") -> bool:
    """Strict greater-than policy: equality (e.g. 28.00) does NOT breach."""
    if campus_code not in CAMPUS_POLICIES:
        raise ValueError(f"unknown campus_code: {campus_code}")
    limit = TEMP_LIMIT if campus_code == "MAIN_CAMPUS" else CAMPUS_POLICIES[campus_code]["temp_limit"]
    return value >= limit


def valid_duration(minutes: int, campus_code: str = "MAIN_CAMPUS") -> bool:
    """Booking duration policy: 0 < minutes <= max_duration."""
    if campus_code not in CAMPUS_POLICIES:
        raise ValueError(f"unknown campus_code: {campus_code}")
    limit = MAX_MINUTES if campus_code == "MAIN_CAMPUS" else CAMPUS_POLICIES[campus_code]["max_duration"]
    return 0 < minutes <= limit


def overlaps(s1: int, e1: int, s2: int, e2: int) -> bool:
    """Half-open interval overlap check [s, e): back-to-back adjacent bookings are allowed."""
    if e1 <= s1 or e2 <= s2:
        raise ValueError("end time must be greater than start time")
    return s1 < e2 and s2 < e1


def sla_deadline(created_utc: datetime, priority_level: str) -> datetime:
    """Deterministic UTC SLA deadline calculation by priority level."""
    if priority_level not in SLA_HOURS:
        raise ValueError(f"unknown priority level: {priority_level}")
    if created_utc.tzinfo is None:
        created_utc = created_utc.replace(tzinfo=timezone.utc)
    return created_utc.astimezone(timezone.utc) + timedelta(hours=SLA_HOURS[priority_level])


def is_sla_overdue(now_utc: datetime, deadline_utc: datetime) -> bool:
    """Equality boundary rule: now == deadline is on-time (False); now > deadline is overdue (True)."""
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    if deadline_utc.tzinfo is None:
        deadline_utc = deadline_utc.replace(tzinfo=timezone.utc)
    return now_utc > deadline_utc


class _LockedCursor:
    def __init__(self, cursor: sqlite3.Cursor, lock: threading.RLock):
        self._cursor = cursor
        self._lock = lock

    def fetchone(self):
        with self._lock:
            return self._cursor.fetchone()

    def fetchall(self):
        with self._lock:
            return self._cursor.fetchall()

    def __iter__(self):
        with self._lock:
            rows = self._cursor.fetchall()
        return iter(rows)

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self) -> int:
        return self._cursor.lastrowid


class _ThreadSafeConnection:
    """Serializes multi-threaded FastAPI worker pool access to a single SQLite connection."""

    def __init__(self, path: str):
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False, timeout=30.0)

    def execute(self, sql: str, params: tuple = ()):
        with self._lock:
            return _LockedCursor(self._conn.execute(sql, params), self._lock)

    def executescript(self, sql: str):
        with self._lock:
            return self._conn.executescript(sql)

    def commit(self):
        with self._lock:
            self._conn.commit()

    def rollback(self):
        with self._lock:
            self._conn.rollback()

    def iterdump(self):
        with self._lock:
            return list(self._conn.iterdump())

    def backup(self, target):
        with self._lock:
            self._conn.backup(target)

    def close(self):
        with self._lock:
            self._conn.close()


class Store:
    def __init__(self, path: str = ":memory:"):
        self.path = path
        self.db = _ThreadSafeConnection(path)
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets(
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                state TEXT NOT NULL,
                version INTEGER NOT NULL,
                notes TEXT,
                source TEXT,
                event_id TEXT,
                priority TEXT DEFAULT 'M3',
                category TEXT DEFAULT 'Manual Review',
                campus_code TEXT DEFAULT 'MAIN_CAMPUS',
                policy_version TEXT DEFAULT 'v1',
                sync_status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, event_id)
            );
            CREATE TABLE IF NOT EXISTS audit(
                id INTEGER PRIMARY KEY,
                ticket_id INTEGER,
                from_state TEXT,
                to_state TEXT,
                actor TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS bookings(
                id INTEGER PRIMARY KEY,
                facility TEXT,
                start_min INTEGER,
                end_min INTEGER,
                status TEXT,
                requester TEXT DEFAULT 'faculty',
                campus_code TEXT DEFAULT 'MAIN_CAMPUS',
                policy_version TEXT DEFAULT 'v1',
                sync_status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
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
        for code, pol in CAMPUS_POLICIES.items():
            self.db.execute(
                "INSERT OR IGNORE INTO policies(campus_code, policy_version, max_duration, temp_limit) VALUES (?,?,?,?)",
                (code, pol["policy_version"], pol["max_duration"], pol["temp_limit"]),
            )
        self.db.commit()

    def create_ticket(
        self,
        title: str,
        source: str = None,
        event_id: str = None,
        impact: str = "Medium",
        urgency: str = "Medium",
        campus_code: str = "MAIN_CAMPUS",
        sync_status: str = "Pending",
    ) -> int:
        if not title or not title.strip():
            raise ValueError("title required")
        if campus_code not in CAMPUS_POLICIES:
            raise ValueError(f"unknown campus_code: {campus_code}")
        prio = priority(impact, urgency)
        cat = classify(title)
        pol_ver = CAMPUS_POLICIES[campus_code]["policy_version"]
        with self.db._lock:
            if source is not None and event_id is not None:
                cur = self.db.execute(
                    "INSERT OR IGNORE INTO tickets(title,state,version,source,event_id,priority,category,campus_code,policy_version,sync_status) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (title.strip(), "New", 1, source, event_id, prio, cat, campus_code, pol_ver, sync_status),
                )
                self.db.commit()
                row = self.db.execute(
                    "SELECT id FROM tickets WHERE source=? AND event_id=?",
                    (source, event_id),
                ).fetchone()
                return row[0]
            cur = self.db.execute(
                "INSERT INTO tickets(title,state,version,source,event_id,priority,category,campus_code,policy_version,sync_status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (title.strip(), "New", 1, source, event_id, prio, cat, campus_code, pol_ver, sync_status),
            )
            self.db.commit()
            return cur.lastrowid

    def count(self, table: str = "tickets") -> int:
        queries = {
            "tickets": "SELECT COUNT(*) FROM tickets",
            "audit": "SELECT COUNT(*) FROM audit",
            "bookings": "SELECT COUNT(*) FROM bookings",
            "policies": "SELECT COUNT(*) FROM policies",
            "integration_outbox": "SELECT COUNT(*) FROM integration_outbox",
        }
        if table not in queries:
            raise ValueError(f"invalid table: {table}")
        return self.db.execute(queries[table]).fetchone()[0]

    def state(self, tid: int):
        return self.db.execute(
            "SELECT state, version FROM tickets WHERE id=?", (tid,)
        ).fetchone()

    def transition(
        self,
        tid: int,
        target: str,
        expected_version: int,
        role: str,
        notes: str = None,
    ) -> int:
        if role not in STAFF:
            raise PermissionError("role not permitted")
        row = self.state(tid)
        if not row:
            raise KeyError(f"ticket {tid} not found")
        state, version = row
        if target not in TRANSITIONS[state]:
            raise ValueError("invalid transition %s -> %s" % (state, target))
        if target == "Resolved" and not (notes and notes.strip()):
            raise ValueError("resolution notes required")
        cur = self.db.execute(
            "UPDATE tickets SET state=?, version=version+1, notes=COALESCE(?,notes) "
            "WHERE id=? AND version=?",
            (target, notes, tid, expected_version),
        )
        if cur.rowcount != 1:
            self.db.rollback()
            raise RuntimeError("stale version")
        self.db.execute(
            "INSERT INTO audit(ticket_id,from_state,to_state,actor) VALUES (?,?,?,?)",
            (tid, state, target, role),
        )
        self.db.commit()
        return version + 1

    def audit_count(self, tid: int) -> int:
        return self.db.execute(
            "SELECT COUNT(*) FROM audit WHERE ticket_id=?", (tid,)
        ).fetchone()[0]

    def request_booking(
        self,
        facility: str,
        start: int,
        end: int,
        requester: str = "faculty",
        campus_code: str = "MAIN_CAMPUS",
        sync_status: str = "Pending",
    ) -> int:
        if not facility or not facility.strip():
            raise ValueError("facility required")
        if not valid_duration(end - start, campus_code=campus_code):
            raise ValueError("duration outside policy")
        for s, e in self.db.execute(
            "SELECT start_min,end_min FROM bookings WHERE facility=? "
            "AND status IN ('Pending','Approved') AND campus_code=?",
            (facility, campus_code),
        ):
            if overlaps(start, end, s, e):
                raise RuntimeError("overlapping booking")
        pol_ver = CAMPUS_POLICIES[campus_code]["policy_version"]
        cur = self.db.execute(
            "INSERT INTO bookings(facility,start_min,end_min,status,requester,campus_code,policy_version,sync_status) "
            "VALUES (?,?,?,'Pending',?,?,?,?)",
            (facility, start, end, requester, campus_code, pol_ver, sync_status),
        )
        self.db.commit()
        return cur.lastrowid

    def approve_booking(self, bid: int, role: str):
        if role not in APPROVERS:
            raise PermissionError("role not permitted")
        cur = self.db.execute(
            "UPDATE bookings SET status='Approved' WHERE id=?", (bid,)
        )
        if cur.rowcount != 1:
            raise KeyError(f"booking {bid} not found")
        self.db.commit()

    def booking_status(self, bid: int) -> str:
        row = self.db.execute(
            "SELECT status FROM bookings WHERE id=?", (bid,)
        ).fetchone()
        if not row:
            raise KeyError(f"booking {bid} not found")
        return row[0]
