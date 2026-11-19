"""FastAPI Service for the Smart Campus Facility and Maintenance Platform."""
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.auth import get_current_actor
from app.integrations import enqueue_and_attempt_sync, process_outbox_entry
from campus_model import (
    APPROVERS,
    CAMPUS_POLICIES,
    STAFF,
    Store,
    breached,
    classify,
    is_sla_overdue,
    priority,
    sla_deadline,
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_db_path() -> str:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./campus_platform.db")
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "", 1)
    return os.environ.get("SQLITE_PATH", "./campus_platform.db")


_STORE: Optional[Store] = None


def get_store() -> Store:
    global _STORE
    if _STORE is None:
        _STORE = Store(get_db_path())
    return _STORE


def set_store(custom_store: Store) -> None:
    global _STORE
    _STORE = custom_store


app = FastAPI(
    title="Smart Campus Facility and Maintenance Platform",
    version=os.environ.get("APP_VERSION", "v1.0.0"),
    description="Risk-based campus facility booking, sensor intake, maintenance SLA, and DevOps hub.",
)


class BookingCreateV1(BaseModel):
    facility: str = Field(..., min_length=1)
    start_min: int
    end_min: int
    role: Optional[str] = None  # Ignored: server derives role from authenticated token


class BookingCreateV2(BaseModel):
    facility: str = Field(..., min_length=1)
    start_min: int
    end_min: int
    campus_code: str = Field(default="MAIN_CAMPUS")
    role: Optional[str] = None  # Ignored: server derives role from authenticated token


class BookingApproveRequest(BaseModel):
    notes: Optional[str] = None
    role: Optional[str] = None  # Ignored: anti-spoofing defence


class SensorEventRequest(BaseModel):
    source: str = Field(..., min_length=1)
    event_id: str = Field(..., min_length=1)
    facility: str = Field(..., min_length=1)
    temperature: float
    impact: str = "High"
    urgency: str = "High"
    campus_code: str = "MAIN_CAMPUS"


class TicketCreateRequest(BaseModel):
    title: str
    impact: str = "Medium"
    urgency: str = "Medium"
    campus_code: str = "MAIN_CAMPUS"


class TicketTransitionRequest(BaseModel):
    target_state: str
    expected_version: int
    notes: Optional[str] = None
    role: Optional[str] = None  # Ignored: server derives role strictly from signed token


@app.get("/health")
def health_check() -> Dict[str, Any]:
    if os.environ.get("SIMULATE_BROKEN_RELEASE", "false").lower() == "true":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulated faulty release startup check failure",
        )
    return {
        "status": "healthy",
        "version": os.environ.get("APP_VERSION", "v1.0.0"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def readiness_check(store: Store = Depends(get_store)) -> Dict[str, Any]:
    if os.environ.get("SIMULATE_BROKEN_RELEASE", "false").lower() == "true":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulated broken release readiness gate failure",
        )
    policy_count = store.count("policies")
    return {
        "status": "ready",
        "version": os.environ.get("APP_VERSION", "v1.0.0"),
        "database": "connected",
        "policies_loaded": policy_count,
        "bookings_count": store.count("bookings"),
        "tickets_count": store.count("tickets"),
        "audit_count": store.count("audit"),
    }


@app.post("/api/v1/bookings", status_code=status.HTTP_201_CREATED)
def create_booking_v1(
    payload: BookingCreateV1,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    """Legacy v1 booking endpoint: defaults to MAIN_CAMPUS (v1 policy) for backward compatibility."""
    try:
        bid = store.request_booking(
            facility=payload.facility,
            start=payload.start_min,
            end=payload.end_min,
            requester=actor["username"],
            campus_code="MAIN_CAMPUS",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    sync_res = enqueue_and_attempt_sync(
        store,
        entity_type="booking",
        entity_id=bid,
        target_system="calendar",
        idempotency_key=f"cal-booking-{bid}",
    )
    return {
        "id": bid,
        "facility": payload.facility,
        "start_min": payload.start_min,
        "end_min": payload.end_min,
        "status": store.booking_status(bid),
        "requester": actor["username"],
        "actor_role": actor["role"],
        "campus_code": "MAIN_CAMPUS",
        "policy_version": "v1",
        "sync_status": "Synced" if sync_res["status"] == "Synced" else "Pending",
    }


@app.get("/api/v1/bookings")
def list_bookings_v1(
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    rows = store.db.execute(
        "SELECT id, facility, start_min, end_min, status, requester, campus_code, policy_version, sync_status "
        "FROM bookings ORDER BY id ASC"
    ).fetchall()
    return {
        "api_version": "v1",
        "count": len(rows),
        "items": [
            {
                "id": r[0],
                "facility": r[1],
                "start_min": r[2],
                "end_min": r[3],
                "status": r[4],
                "requester": r[5],
                "campus_code": r[6],
                "policy_version": r[7],
                "sync_status": r[8],
            }
            for r in rows
        ],
    }


@app.post("/api/v2/bookings", status_code=status.HTTP_201_CREATED)
def create_booking_v2(
    payload: BookingCreateV2,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    """Day-4 revised v2 booking endpoint supporting campus-specific versioned duration limits."""
    try:
        bid = store.request_booking(
            facility=payload.facility,
            start=payload.start_min,
            end=payload.end_min,
            requester=actor["username"],
            campus_code=payload.campus_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    sync_res = enqueue_and_attempt_sync(
        store,
        entity_type="booking",
        entity_id=bid,
        target_system="calendar",
        idempotency_key=f"cal-booking-{bid}",
    )
    pol = CAMPUS_POLICIES[payload.campus_code]
    return {
        "api_version": "v2",
        "id": bid,
        "facility": payload.facility,
        "start_min": payload.start_min,
        "end_min": payload.end_min,
        "duration_min": payload.end_min - payload.start_min,
        "status": store.booking_status(bid),
        "requester": actor["username"],
        "campus_code": payload.campus_code,
        "policy_version": pol["policy_version"],
        "max_duration_allowed": pol["max_duration"],
        "sync_status": "Synced" if sync_res["status"] == "Synced" else "Pending",
        "outbox_status": sync_res["status"],
    }


@app.get("/api/v2/bookings")
def list_bookings_v2(
    campus_code: Optional[str] = None,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    if campus_code:
        rows = store.db.execute(
            "SELECT id, facility, start_min, end_min, status, requester, campus_code, policy_version, sync_status "
            "FROM bookings WHERE campus_code=? ORDER BY id ASC",
            (campus_code,),
        ).fetchall()
    else:
        rows = store.db.execute(
            "SELECT id, facility, start_min, end_min, status, requester, campus_code, policy_version, sync_status "
            "FROM bookings ORDER BY id ASC"
        ).fetchall()
    return {
        "api_version": "v2",
        "count": len(rows),
        "items": [
            {
                "id": r[0],
                "facility": r[1],
                "start_min": r[2],
                "end_min": r[3],
                "status": r[4],
                "requester": r[5],
                "campus_code": r[6],
                "policy_version": r[7],
                "sync_status": r[8],
            }
            for r in rows
        ],
    }


@app.post("/api/v1/bookings/{booking_id}/approve")
def approve_booking_endpoint(
    booking_id: int,
    payload: Optional[BookingApproveRequest] = None,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    """Approve a booking. Derives role strictly from authenticated token, never from request body."""
    if actor["role"] not in APPROVERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor['role']}' is not authorized to approve facility bookings",
        )
    try:
        store.approve_booking(booking_id, actor["role"])
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {
        "id": booking_id,
        "status": store.booking_status(booking_id),
        "approved_by": actor["username"],
        "approved_role": actor["role"],
    }


@app.post("/api/v1/sensors/events")
def ingest_sensor_event(
    payload: SensorEventRequest,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    """Ingest sensor alert with strict greater-than threshold and (source, event_id) idempotency."""
    try:
        is_breach = breached(payload.temperature, campus_code=payload.campus_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not is_breach:
        return {
            "breached": False,
            "ticket_created": False,
            "ticket_id": None,
            "temperature": payload.temperature,
            "campus_code": payload.campus_code,
            "policy_version": CAMPUS_POLICIES[payload.campus_code]["policy_version"],
        }

    title = f"HVAC temperature alert ({payload.temperature}C) in {payload.facility}"
    tid = store.create_ticket(
        title=title,
        source=payload.source,
        event_id=payload.event_id,
        impact=payload.impact,
        urgency=payload.urgency,
        campus_code=payload.campus_code,
    )
    sync_res = enqueue_and_attempt_sync(
        store,
        entity_type="ticket",
        entity_id=tid,
        target_system="issue-tracker",
        idempotency_key=f"issue-sensor-{payload.source}-{payload.event_id}",
    )
    row = store.db.execute(
        "SELECT state, version, priority, category, campus_code, policy_version, sync_status FROM tickets WHERE id=?",
        (tid,),
    ).fetchone()
    return {
        "breached": True,
        "ticket_created": True,
        "ticket_id": tid,
        "state": row[0],
        "version": row[1],
        "priority": row[2],
        "category": row[3],
        "campus_code": row[4],
        "policy_version": row[5],
        "sync_status": row[6],
        "outbox_status": sync_res["status"],
    }


@app.post("/api/v1/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket_endpoint(
    payload: TicketCreateRequest,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    try:
        tid = store.create_ticket(
            title=payload.title,
            impact=payload.impact,
            urgency=payload.urgency,
            campus_code=payload.campus_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    sync_res = enqueue_and_attempt_sync(
        store,
        entity_type="ticket",
        entity_id=tid,
        target_system="issue-tracker",
        idempotency_key=f"issue-ticket-{tid}",
    )
    now_utc = datetime.now(timezone.utc)
    prio = priority(payload.impact, payload.urgency)
    deadline = sla_deadline(now_utc, prio)
    return {
        "id": tid,
        "title": payload.title.strip(),
        "state": "New",
        "version": 1,
        "priority": prio,
        "category": classify(payload.title),
        "campus_code": payload.campus_code,
        "policy_version": CAMPUS_POLICIES[payload.campus_code]["policy_version"],
        "sla_deadline_utc": deadline.isoformat(),
        "sla_overdue": is_sla_overdue(now_utc, deadline),
        "sync_status": "Synced" if sync_res["status"] == "Synced" else "Pending",
    }


@app.get("/api/v1/tickets")
def list_tickets_endpoint(
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    if actor["role"] == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student role cannot access internal maintenance ticket ledger",
        )
    rows = store.db.execute(
        "SELECT id, title, state, version, notes, source, event_id, priority, category, campus_code, policy_version, sync_status "
        "FROM tickets ORDER BY id ASC"
    ).fetchall()
    return {
        "count": len(rows),
        "items": [
            {
                "id": r[0],
                "title": r[1],
                "state": r[2],
                "version": r[3],
                "notes": r[4],
                "source": r[5],
                "event_id": r[6],
                "priority": r[7],
                "category": r[8],
                "campus_code": r[9],
                "policy_version": r[10],
                "sync_status": r[11],
            }
            for r in rows
        ],
    }


@app.post("/api/v1/tickets/{ticket_id}/transition")
def transition_ticket_endpoint(
    ticket_id: int,
    payload: TicketTransitionRequest,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    if actor["role"] not in STAFF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor['role']}' is not authorized to transition maintenance tickets",
        )
    try:
        new_ver = store.transition(
            tid=ticket_id,
            target=payload.target_state,
            expected_version=payload.expected_version,
            role=actor["role"],
            notes=payload.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    state, ver = store.state(ticket_id)
    return {
        "ticket_id": ticket_id,
        "state": state,
        "version": new_ver,
        "actor": actor["username"],
        "role": actor["role"],
        "audit_count": store.audit_count(ticket_id),
    }


@app.get("/api/v1/tickets/{ticket_id}/audit")
def get_ticket_audit(
    ticket_id: int,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    if actor["role"] == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student role cannot access internal ticket audit trail",
        )
    rows = store.db.execute(
        "SELECT id, ticket_id, from_state, to_state, actor, created_at FROM audit WHERE ticket_id=? ORDER BY id ASC",
        (ticket_id,),
    ).fetchall()
    return {
        "ticket_id": ticket_id,
        "audit_count": len(rows),
        "events": [
            {
                "id": r[0],
                "ticket_id": r[1],
                "from_state": r[2],
                "to_state": r[3],
                "actor": r[4],
                "created_at": r[5],
            }
            for r in rows
        ],
    }


@app.get("/api/v1/facilities/restricted")
def get_restricted_facilities(
    actor: Dict[str, str] = Depends(get_current_actor),
) -> Dict[str, Any]:
    if actor["role"] == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student role is prohibited from viewing restricted laboratory access schedules",
        )
    return {
        "restricted_facilities": [
            {"code": "Lab-204", "campus": "MAIN_CAMPUS", "classification": "Biosafety Level 2", "approver_required": True},
            {"code": "Cryo-Annex-01", "campus": "RESEARCH_ANNEX", "classification": "Cryogenic Cleanroom", "approver_required": True},
        ]
    }


@app.get("/api/v1/outbox")
def list_outbox_entries(
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    if actor["role"] == "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    rows = store.db.execute(
        "SELECT id, entity_type, entity_id, target_system, idempotency_key, status, attempts, remote_id, last_error "
        "FROM integration_outbox ORDER BY id ASC"
    ).fetchall()
    return {
        "count": len(rows),
        "items": [
            {
                "id": r[0],
                "entity_type": r[1],
                "entity_id": r[2],
                "target_system": r[3],
                "idempotency_key": r[4],
                "status": r[5],
                "attempts": r[6],
                "remote_id": r[7],
                "last_error": r[8],
            }
            for r in rows
        ],
    }


@app.post("/api/v1/outbox/{idempotency_key}/retry")
def retry_outbox_key(
    idempotency_key: str,
    actor: Dict[str, str] = Depends(get_current_actor),
    store: Store = Depends(get_store),
) -> Dict[str, Any]:
    if actor["role"] not in STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required for outbox retry")
    try:
        return process_outbox_entry(store, idempotency_key)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.get("/load-report", response_class=HTMLResponse)
def view_load_report() -> HTMLResponse:
    report_path = BASE_DIR.parent / "evidence" / "logs" / "load_test_report.html"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Load report not generated yet")
    return HTMLResponse(content=report_path.read_text(encoding="utf-8"))


@app.get("/terminal-view/{log_name}", response_class=HTMLResponse)
def view_terminal_log(log_name: str, title: str = "Terminal Execution Output", cmd: str = "") -> HTMLResponse:
    import html as html_mod
    safe_name = Path(log_name).name
    log_path = BASE_DIR.parent / "evidence" / "logs" / safe_name
    if not log_path.exists():
        raise HTTPException(status_code=404, detail=f"Log {safe_name} not found")
    raw_text = log_path.read_text(encoding="utf-8", errors="replace")
    escaped_lines = []
    for line in raw_text.splitlines():
        esc = html_mod.escape(line)
        if "PASSED" in line or "SMOKE PASS" in line or "MIGRATION_SUCCESS" in line or "0 Errors" in line:
            esc = f'<span style="color:#4ade80;font-weight:700;">{esc}</span>'
        elif "FAILED" in line or "AssertionError" in line or "E       " in line or "ALERT" in line or "403 Forbidden" in line:
            esc = f'<span style="color:#f87171;font-weight:700;">{esc}</span>'
        elif line.startswith("===") or line.startswith("---") or line.startswith("[STEP") or line.startswith("[SMOKE") or line.startswith("STAGE"):
            esc = f'<span style="color:#38bdf8;font-weight:700;">{esc}</span>'
        escaped_lines.append(esc)
    formatted = "\n".join(escaped_lines)
    page = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{html_mod.escape(title)}</title>
<style>
  body {{ background: #090d16; color: #e2e8f0; font-family: "Cascadia Code", "Consolas", "Courier New", monospace; margin: 0; padding: 18px 24px; }}
  .term-window {{ background: #0f172a; border: 1px solid #334155; border-radius: 10px; box-shadow: 0 12px 28px rgba(0,0,0,0.45); overflow: hidden; }}
  .term-bar {{ background: #1e293b; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .dots {{ display: flex; gap: 7px; }}
  .dot {{ width: 11px; height: 11px; border-radius: 50%; display: inline-block; }}
  .dot.r {{ background: #ef4444; }} .dot.y {{ background: #f59e0b; }} .dot.g {{ background: #22c55e; }}
  .term-title {{ font-size: 0.84rem; font-weight: 600; color: #cbd5e1; }}
  .term-meta {{ font-size: 0.76rem; color: #94a3b8; }}
  .cmd-line {{ background: #111827; padding: 9px 18px; border-bottom: 1px solid #1e293b; color: #fcd34d; font-size: 0.82rem; }}
  pre {{ margin: 0; padding: 14px 18px; font-size: 0.77rem; line-height: 1.38; white-space: pre-wrap; word-break: break-word; color: #e2e8f0; }}
</style>
</head>
<body>
  <div class="term-window">
    <div class="term-bar">
      <div class="dots"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span></div>
      <div class="term-title">{html_mod.escape(title)}</div>
      <div class="term-meta">SIMATS CSA10 Assignment 4 | Host: Windows 11 / Python 3.13.9</div>
    </div>
    <div class="cmd-line">PS C:\\smart-campus-facility-devops&gt; {html_mod.escape(cmd)}</div>
    <pre>{formatted}</pre>
  </div>
</body>
</html>"""
    return HTMLResponse(content=page)


@app.get("/", response_class=HTMLResponse)
def dashboard_ui(request: Request, store: Store = Depends(get_store)):
    bookings = store.db.execute(
        "SELECT id, facility, start_min, end_min, status, requester, campus_code, policy_version, sync_status "
        "FROM bookings ORDER BY id DESC LIMIT 10"
    ).fetchall()
    tickets = store.db.execute(
        "SELECT id, title, state, version, priority, category, campus_code, policy_version, sync_status, notes "
        "FROM tickets ORDER BY id DESC LIMIT 10"
    ).fetchall()
    audits = store.db.execute(
        "SELECT id, ticket_id, from_state, to_state, actor, created_at FROM audit ORDER BY id DESC LIMIT 10"
    ).fetchall()
    policies = store.db.execute(
        "SELECT campus_code, policy_version, max_duration, temp_limit FROM policies ORDER BY campus_code ASC"
    ).fetchall()
    outbox = store.db.execute(
        "SELECT id, entity_type, entity_id, target_system, idempotency_key, status, attempts, remote_id, last_error "
        "FROM integration_outbox ORDER BY id DESC LIMIT 10"
    ).fetchall()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "version": os.environ.get("APP_VERSION", "v1.0.0"),
            "bookings": bookings,
            "tickets": tickets,
            "audits": audits,
            "policies": policies,
            "outbox": outbox,
            "counts": {
                "bookings": store.count("bookings"),
                "tickets": store.count("tickets"),
                "audit": store.count("audit"),
                "outbox": store.count("integration_outbox"),
            },
        },
    )
