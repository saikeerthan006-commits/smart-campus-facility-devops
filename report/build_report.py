"""Generates the publication-ready Word report:
report/CSA10_Assignment4_Smart_Campus_Report.docx
Mirrors the academic formatting of Q1-Assignment4-Word.pdf with 100% real executed evidence
and all 16 verified screenshots embedded.
"""
from pathlib import Path

import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "evidence" / "screenshots"
LOGS = ROOT / "evidence" / "logs"
OUT_DOCX = ROOT / "report" / "CSA10_Assignment4_Smart_Campus_Report.docx"

NAVY_HEX = "0F172A"
BLUE_HEX = "1E3A8A"
HEADER_BG_HEX = "E2E8F0"
ZEBRA_BG_HEX = "F8FAFC"
CODE_BG_HEX = "F1F5F9"
BORDER_HEX = "CBD5E1"


def set_cell_background(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")
    for m_name, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m_name}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tc_mar.append(node)
    tc_pr.append(tc_mar)


def set_table_borders(table, color_hex: str = BORDER_HEX) -> None:
    tbl_pr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{color_hex}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color_hex}"/>'
        f'<w:left w:val="single" w:sz="6" w:space="0" w:color="{color_hex}"/>'
        f'<w:right w:val="single" w:sz="6" w:space="0" w:color="{color_hex}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f"</w:tblBorders>"
    )
    tbl_pr.append(borders)


def add_page_number_to_run(run) -> None:
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "separate")
    fld_char3 = OxmlElement("w:fldChar")
    fld_char3.set(qn("w:fldCharType"), "end")
    r = run._r
    r.append(fld_char1)
    r.append(instr_text)
    r.append(fld_char2)
    r.append(fld_char3)


def add_heading_1(doc: docx.Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Calibri"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    return p


def add_heading_2(doc: docx.Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Calibri"
    run.font.size = Pt(11.5)
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    return p


def add_body(doc: docx.Document, text: str, bold_prefix: str = "", italic: bool = False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    r = p.add_run(text)
    r.italic = italic
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    return p


def add_styled_table(doc: docx.Document, headers: list[str], rows: list[list[str]]):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    hdr_cells = table.rows[0].cells
    for idx, h_text in enumerate(headers):
        cell = hdr_cells[idx]
        set_cell_background(cell, HEADER_BG_HEX)
        set_cell_margins(cell, top=90, bottom=90, left=110, right=110)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(h_text)
        run.bold = True
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    for r_idx, row_vals in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg = ZEBRA_BG_HEX if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            cell = row_cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=110, right=110)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(str(val))
            run.font.name = "Calibri"
            run.font.size = Pt(9.2)
            if c_idx == 0:
                run.bold = True
            run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(4)
    return table


def add_code_block(doc: docx.Document, title: str, code_text: str):
    if title:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_before = Pt(6)
        p_t.paragraph_format.space_after = Pt(2)
        p_t.paragraph_format.keep_with_next = True
        r_t = p_t.add_run(title)
        r_t.bold = True
        r_t.font.name = "Calibri"
        r_t.font.size = Pt(9.8)
        r_t.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, BORDER_HEX)
    cell = tbl.rows[0].cells[0]
    set_cell_background(cell, CODE_BG_HEX)
    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    r = p.add_run(code_text.strip("\r\n"))
    r.font.name = "Consolas"
    r.font.size = Pt(8.2)
    r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(4)


def add_figure(doc: docx.Document, filename: str, caption: str, width_inches: float = 6.1):
    img_path = SHOTS / filename
    if not img_path.exists():
        raise FileNotFoundError(f"Required screenshot missing: {img_path}")

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True
    run_img = p_img.add_run()
    run_img.add_picture(str(img_path), width=Inches(width_inches))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(8)
    r_cap = p_cap.add_run(caption)
    r_cap.italic = True
    r_cap.font.name = "Calibri"
    r_cap.font.size = Pt(9.2)
    r_cap.font.color.rgb = RGBColor(0x33, 0x41, 0x55)


def build_report() -> None:
    doc = docx.Document()

    # Page margins & Header/Footer setup
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

        hdr = section.header
        p_hdr = hdr.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r_hdr = p_hdr.add_run("SIMATS ENGINEERING | CSA10 SOFTWARE ENGINEERING")
        r_hdr.font.name = "Calibri"
        r_hdr.font.size = Pt(8.8)
        r_hdr.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

        ftr = section.footer
        p_ftr = ftr.paragraphs[0]
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_ftr_lbl = p_ftr.add_run("Page ")
        r_ftr_lbl.font.name = "Calibri"
        r_ftr_lbl.font.size = Pt(9.0)
        r_ftr_num = p_ftr.add_run()
        r_ftr_num.font.name = "Calibri"
        r_ftr_num.font.size = Pt(9.0)
        add_page_number_to_run(r_ftr_num)

    # ---- COVER & TITLE BLOCK ----
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(4)
    r_t1 = p_title.add_run("Software Engineering\nAssignment 4")
    r_t1.bold = True
    r_t1.font.name = "Calibri"
    r_t1.font.size = Pt(20)
    r_t1.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(2)
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run("Testing and DevOps Delivery for the Smart Campus Facility Platform")
    r_sub.bold = True
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    add_styled_table(
        doc,
        ["Candidate Attribute", "Verified Submission Detail"],
        [
            ["Student Name", "Keerthan M"],
            ["Register Number", "1925260006"],
            ["Programme and Section", "B.E. / B.Tech. Artificial Intelligence and Machine Learning (AIML)"],
            ["Course Code & Title", "CSA10 — Software Engineering (CO4, Total Marks: 50)"],
            ["Submission Date", "18/11/2026"],
            ["GitHub Repository URL", "https://github.com/saikeerthan006-commits/smart-campus-facility-devops"],
            ["Passing CI/CD Run URL", "https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577255849"],
            ["Blocked Defective Run URL", "https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577269915"],
        ],
    )

    add_body(
        doc,
        "Implement software testing strategies (unit, integration, regression) and DevOps pipelines using tools such as GitHub Actions, Docker, and Jenkins to validate the reliability, security, and continuous delivery of software systems.",
        bold_prefix="CO4 Outcome Statement: ",
    )
    add_body(
        doc,
        "This report establishes and executes an end-to-end risk-based testing strategy and gated DevOps delivery pipeline for the Smart Campus Facility and Maintenance Platform. It connects a deterministic core domain model (campus_model.py) and a production-structured FastAPI + SQLite/PostgreSQL web application (app/) to 30 automated unit, integration, API security, and Day-4 regression checks, two controlled defect injections, a multi-stage Docker container build, a two-stage GitHub Actions release pipeline, an actual five-stage bounded load and dependency outage experiment, a timed failure-and-rollback recovery rehearsal, and an expand-and-contract database migration.",
    )
    add_body(
        doc,
        "Method: Thirty automated checks (U1–U10, I1–I6, R1–R5, sec_01–sec_04, day4_01–day4_05) and two controlled defect injections were executed against both the standalone SQLite domain store (campus_model.py) and the full FastAPI HTTP service (app/main.py). All workflow runs, Docker multi-stage image builds, Trivy vulnerability scans, smoke journeys, direct API RBAC tests, 50-client bounded load experiments, database backup/rollback rehearsals, and Day-4 expand-and-contract migrations were genuinely executed and verified with real commit SHAs, Docker image digests, raw logs, and live browser screenshots.",
        italic=True,
    )

    add_heading_2(doc, "Problem Statement")
    add_body(
        doc,
        "A university releases frequent changes to its campus facility platform affecting booking-overlap rules, slot-duration limits, sensor thresholds, maintenance SLA rules, ticket transitions, and approval permissions. Application startup alone cannot reveal double bookings, incorrect triage, duplicate processing, unauthorized approvals, or migration failures. We create and implement a risk-based unit, integration, and regression test strategy linked to measurable release acceptance criteria, construct a DevOps pipeline that checks versioned changes, builds containers, blocks defective releases, and verifies deployment, validate reliability, security, and recovery, and adapt the tests and delivery process for campus-specific booking policies, a revised booking API, a database migration, and intermittent calendar and developer-issue synchronization.",
    )

    # =========================================================================
    # TASK 1
    # =========================================================================
    add_heading_1(doc, "Task 1 — Investigate Risks and Define Release Acceptance (5 Marks)")
    add_body(
        doc,
        "The representative service scope covers facility booking creation and approval (/api/v1/bookings and /api/v2/bookings), environmental sensor-alert intake (/api/v1/sensors/events), maintenance ticket triage and lifecycle transitions (/api/v1/tickets and /api/v1/tickets/{id}/transition), immutable audit trail persistence (/api/v1/tickets/{id}/audit), restricted laboratory schedule queries (/api/v1/facilities/restricted), and durable external calendar/issue-tracker synchronization (/api/v1/outbox). Six platform user roles interact with the system: administrator (admin), facility manager (manager), maintenance technician (technician), department approver (approver), faculty member (faculty), and student (student). Sensitive data comprises staff and student identities, HMAC-signed authentication tokens, restricted biosafety/cryogenic laboratory schedules, and immutable operational audit logs. Occupancy forecasting, payment processing, and live physical BMS hardware actuation are explicitly excluded from the release scope.",
        bold_prefix="Service Scope, User Roles, Sensitive Data & Exclusions: ",
    )

    add_heading_2(doc, "1.1 Ranked Risk Register Linked to Release Checks")
    add_body(
        doc,
        "Risks are ranked using an ordinal Likelihood (1–5) × Impact (1–5) score (range 1–25). Scores represent ordinal engineering priority rather than calibrated actuarial probabilities. Critical security authorization and data-loss risks are treated as mandatory release gates even when their estimated likelihood is low.",
    )
    add_styled_table(
        doc,
        ["Risk ID & Failure Mode", "Category", "L × I Score", "Consequence of Failure", "Mandatory Release Gate & Verification Check"],
        [
            [
                "R-01: Duplicate sensor event or network retry creates duplicate tickets",
                "Integration & Reliability",
                "4 × 4 = 16",
                "Maintenance queue flooded with duplicate dispatches for one physical HVAC breach.",
                "Composite UNIQUE(source, event_id) constraint + idempotent outbox key; verified by test_I2 and 50-event replay burst.",
            ],
            [
                "R-02: Overlapping facility booking accepted",
                "Correctness",
                "3 × 5 = 15",
                "Double-booked laboratory causes research schedule collision and safety violation.",
                "Half-open interval [s1, e1) overlap check (s1 < e2 and s2 < e1); verified by test_I4 (overlap rejected, back-to-back allowed).",
            ],
            [
                "R-03: Unauthorized approval or role spoofing on restricted facility",
                "Security (Mandatory Gate)",
                "3 × 5 = 15",
                "Student self-approves restricted BSL-2/Cryogenic lab or mutates ticket state via API.",
                "Server derives role strictly from HMAC Bearer token, ignoring JSON body role claims; verified by test_I3 and test_sec_01..04.",
            ],
            [
                "R-04: Sensor threshold or SLA deadline boundary off-by-one error",
                "Correctness",
                "3 × 4 = 12",
                "False alarm at 28.00°C or premature SLA breach alert at exact deadline timestamp.",
                "Strict greater-than policy (value > limit; now_utc > deadline_utc); verified by test_U6, test_U7, test_U9.",
            ],
            [
                "R-05: Deployed UI or container starts but API/DB workflow fails",
                "Delivery & Operations",
                "3 × 4 = 12",
                "Green container startup masks broken schema, missing secret, or failing transition route.",
                "Gated Stage-2 Docker Compose deployment + authenticated end-to-end scripts/smoke-test.sh journey.",
            ],
            [
                "R-06: Database migration loses historical bookings or audit trail",
                "Data Integrity (Mandatory Gate)",
                "2 × 5 = 10",
                "Irreversible loss of compliance audit history or approved reservations during schema update.",
                "Pre-migration snapshot backup + expand-and-contract migration rehearsal asserting pre_count == post_count (test_day4_02).",
            ],
            [
                "R-07: External calendar or issue tracker outage drops local transaction",
                "Reliability & Integration",
                "4 × 3 = 12",
                "Temporary downstream timeout aborts local booking/ticket or falsely reports Synced.",
                "Durable integration_outbox table preserving local record in Pending state with bounded retry (max=3; test_I6, test_day4_04).",
            ],
        ],
    )

    add_heading_2(doc, "1.2 Measurable Release Acceptance Criteria")
    add_styled_table(
        doc,
        ["Functional / NFR Area", "Measurable Acceptance Criterion (Release Oracle)", "Linked Verification Gate"],
        [
            [
                "Priority Matrix (FR03)",
                "All 9 (Impact, Urgency) cells deterministically return approved SLA level: (High,High)->M1, (High,Medium)->M2, (High,Low)->M3, (Medium,High)->M2, (Medium,Medium)->M3, (Medium,Low)->M4, (Low,High)->M3, (Low,Medium)->M4, (Low,Low)->M4. Any out-of-range value raises ValueError / HTTP 400.",
                "test_U1, test_U2, test_U3, test_U10, test_R1",
            ],
            [
                "Deterministic Triage Classifier (FR04)",
                "Keyword rules match Facilities, HVAC, or AV-Network; zero matches or tied top scores return 'Manual Review'. Explicitly labelled as deterministic keyword rules (not ML).",
                "test_U4, test_U5, test_R2",
            ],
            [
                "Sensor Threshold Policy (FR07)",
                "Strict greater-than comparison: on MAIN_CAMPUS (v1), 27.99°C and 28.00°C return False (no breach); 28.01°C returns True (breach). On RESEARCH_ANNEX (v2), 24.50°C returns False; 24.51°C returns True.",
                "test_U6, test_U7, test_day4_01",
            ],
            [
                "Booking Duration & Overlap (FR05)",
                "0 < duration <= max_duration (180 min on MAIN_CAMPUS v1: 179 and 180 accepted, 0 and 181 rejected; 240 min on RESEARCH_ANNEX v2). Half-open [start, end) allows adjacent back-to-back bookings (e.g., 600–720 and 720–800).",
                "test_U8, test_I4, test_day4_01, test_day4_03",
            ],
            [
                "UTC SLA Deadline Calculation (FR09)",
                "Deterministic UTC offsets (M1: +1h, M2: +4h, M3: +24h, M4: +72h). Explicit equality rule: now_utc == deadline_utc is on-time (overdue=False); now_utc > deadline_utc (+1s) is overdue (overdue=True).",
                "test_U9",
            ],
            [
                "Ticket Lifecycle & Concurrency (FR06)",
                "Strictly ordered transitions: New -> Assigned -> In Progress -> Resolved -> Closed. Resolved requires non-empty notes. Optimistic lock expected_version mismatch rejected with RuntimeError / HTTP 409. Every transition appends an immutable audit row.",
                "test_I1, test_R3, test_R4, test_R5, test_I5",
            ],
            [
                "RBAC & Anti-Spoofing Security (FR01/NFR03)",
                "Actor role derived exclusively from HMAC-SHA256 Bearer token signature. Student role receives HTTP 403 on booking approval (even with spoofed {'role':'approver'} payload), ticket transitions, and restricted facility queries; DB state remains unchanged.",
                "test_I3, test_sec_01, test_sec_02, test_sec_03, test_sec_04",
            ],
        ],
    )

    add_heading_2(doc, "1.3 Testing and Delivery Tool Comparison & Justification")
    add_styled_table(
        doc,
        ["Evaluation Dimension", "Option A: Pytest + GitHub Actions + Docker (Selected)", "Option B: JUnit / Jest + Self-Hosted Jenkins + VM"],
        [
            [
                "Language & Runtime Alignment",
                "Native fit for Python 3.12/3.13 FastAPI & SQLite/PostgreSQL backend; fixtures (tmp_path, monkeypatch, TestClient) isolate DB state per test.",
                "Mismatched runtime: JUnit targets JVM and Jest targets Node.js, requiring cross-process wrappers to test Python domain logic.",
            ],
            [
                "CI/CD Hosting & Maintenance Overhead",
                "Zero server maintenance: GitHub-hosted ubuntu-latest runners natively support service containers (postgres:16-alpine) and Docker Compose.",
                "Requires provisioning, patching, and securing a dedicated Jenkins controller, agent executors, and credential plugins.",
            ],
            [
                "Repeatability & Artifact Traceability",
                "Declarative .github/workflows/ci.yml versioned in Git; immutable Docker image tags (campus-backend:${{ github.sha }}) and SHA256 digests.",
                "Jenkinsfile + mutable host environment risks configuration drift across build agents unless heavily containerized.",
            ],
            [
                "Cost & Academic Resource Fit",
                "Free tier for public university repositories with built-in Actions Secrets and artifact storage.",
                "Incurs persistent cloud VM or lab server hosting cost and administrative overhead.",
            ],
        ],
    )
    add_body(
        doc,
        "Option A (Pytest + GitHub Actions + Docker Compose) is selected because the application and test model are written in Python, our repository is hosted on GitHub, and GitHub-hosted Ubuntu runners execute isolated PostgreSQL service containers, multi-stage Docker builds, Trivy scans, and smoke checks without maintaining a dedicated Jenkins build server.",
        bold_prefix="Justification: ",
    )

    # =========================================================================
    # TASK 2
    # =========================================================================
    add_heading_1(doc, "Task 2 — Create a Layered Test Strategy (7 Marks)")
    add_body(
        doc,
        "Our test strategy separates fast, isolated rule verification from real component interaction while treating regression as a cross-cutting purpose rather than a third physical execution layer:",
    )
    add_body(
        doc,
        "Isolate pure domain arithmetic and deterministic policy functions in campus_model.py (9-cell priority matrix, keyword classification, temperature threshold comparisons, slot duration limits, half-open interval overlap math, and UTC SLA deadline equality boundaries) with zero file I/O or network dependencies.",
        bold_prefix="1. Unit Testing Layer (U1–U10): ",
    )
    add_body(
        doc,
        "Exercise real component interactions across the SQLite/PostgreSQL persistence layer (Store), file close/reopen durability, composite unique constraints, FastAPI HTTP endpoints, HMAC Bearer token middleware, and the external calendar/issue-tracker outbox adapter using isolated per-test database files (tmp_path).",
        bold_prefix="2. Integration Testing Layer (I1–I6, sec_01–sec_04): ",
    )
    add_body(
        doc,
        "Regression testing is the purpose of protecting previously working critical behaviours against unintended breakage as new policies, schemas, and APIs are introduced. Regression checks intentionally span both unit checks (R1 priority mapping, R2 unknown terminology fallback, day4_01 policy thresholds) and database/HTTP integration checks (R3 resolution notes enforcement, R4 optimistic lock stale-version rejection, R5 empty title rejection, day4_02..05 migration and v1 compatibility).",
        bold_prefix="3. Regression Testing Purpose (R1–R5, day4_01–day4_05): ",
    )

    add_heading_2(doc, "2.1 Executable Test Case Specifications")
    add_styled_table(
        doc,
        ["Test ID", "Layer / Purpose", "Test Inputs & Action", "Setup & Dependencies", "Expected Oracle", "Cleanup"],
        [
            ["U1", "Unit", "priority('High', 'High')", "Pure function call", "Returns 'M1'", "Stateless"],
            ["U2", "Unit", "priority('Low', 'Low')", "Pure function call", "Returns 'M4'", "Stateless"],
            ["U3", "Unit (Negative)", "priority('Critical', 'High')", "Pure function call", "Raises ValueError('invalid matrix input')", "Stateless"],
            ["U4", "Unit", "classify('Water leak from lab ceiling')", "Keyword dictionary", "Returns 'Facilities'", "Stateless"],
            ["U5", "Unit (Boundary)", "classify('Leak and projector fault')", "Tied 1:1 keyword score", "Returns 'Manual Review'", "Stateless"],
            ["U6", "Unit (Boundary)", "breached(28.0), breached(28.01)", "MAIN_CAMPUS TEMP_LIMIT=28.0", "Returns (False, True) under strict > rule", "Stateless"],
            ["U7", "Unit (Boundary)", "breached(27.99)", "MAIN_CAMPUS TEMP_LIMIT=28.0", "Returns False", "Stateless"],
            ["U8", "Unit (Boundary)", "valid_duration(0, 179, 180, 181)", "MAX_MINUTES=180", "0->False, 179->True, 180->True, 181->False", "Stateless"],
            ["U9", "Unit (Boundary)", "sla_deadline & is_sla_overdue at -1s, 0s, +1s", "Fixed UTC 2026-11-18T08:00Z, M1 (+1h)", "Deadline 09:00Z; -1s->False, 0s->False, +1s->True", "Stateless"],
            ["U10", "Unit", "All 9 (Impact, Urgency) pairs", "MATRIX lookup table", "Exact match across all 9 cells", "Stateless"],
            ["I1", "Integration", "Create ticket; transition New->Assigned->In Progress->Resolved->Closed; close & reopen DB file", "File-backed SQLite in pytest tmp_path", "Reopened DB state == ('Closed', 5) and audit_count == 4", "tmp_path auto-removed"],
            ["I2", "Integration", "Submit create_ticket('Temp high','sensor-7','evt-1') 5 times", "Isolated SQLite Store", "len(returned_ids) == 1 and ticket count == 1", "In-memory teardown"],
            ["I3", "Integration (Security)", "approve_booking(b, 'student') on Pending booking", "Isolated SQLite Store", "Raises PermissionError; booking remains 'Pending'", "In-memory teardown"],
            ["I4", "Integration (Boundary)", "Book 600–720; attempt overlap 700–800; book adjacent 720–800", "Isolated SQLite Store", "700–800 raises RuntimeError; 720–800 succeeds (count==2)", "In-memory teardown"],
            ["I5", "Integration (HTTP E2E)", "POST /api/v1/bookings -> approve -> sensor event -> 4 transitions -> GET audit", "FastAPI TestClient + file SQLite DB + signed tokens", "HTTP 201/200 at each step; final audit_count == 4", "Close DB & tmp_path"],
            ["I6", "Integration (Outage)", "POST /api/v1/bookings with EXTERNAL_SYNC_FAIL=true", "FastAPI TestClient + monkeypatch env", "HTTP 201 Created locally; sync_status == 'Pending' (not Synced)", "Close DB & reset env"],
            ["R1", "Regression (Unit)", "priority('High', 'Medium')", "Core matrix baseline", "Returns 'M2'", "Stateless"],
            ["R2", "Regression (Unit)", "classify('strange noise somewhere')", "Zero keyword match", "Returns 'Manual Review'", "Stateless"],
            ["R3", "Regression (Integ)", "Transition In Progress -> Resolved with whitespace notes '   '", "Isolated SQLite Store at version 3", "Raises ValueError; state remains 'In Progress'", "In-memory teardown"],
            ["R4", "Regression (Integ)", "Transition Assigned -> In Progress with stale expected_version=1", "Isolated SQLite Store at version 2", "Raises RuntimeError('stale version'); state ('Assigned', 2)", "In-memory teardown"],
            ["R5", "Regression (Integ)", "create_ticket('   ') with blank title", "Isolated SQLite Store", "Raises ValueError('title required'); count == 0", "In-memory teardown"],
            ["sec_01..04", "Security API (Integ)", "Student spoofing {'role':'approver'}, restricted lab/ticket access, 6-role matrix, tampered token", "FastAPI TestClient + HMAC Bearer tokens", "HTTP 403 for student/unauthorized roles; HTTP 401 for bad signature; DB unchanged", "Close DB & tmp_path"],
            ["day4_01..05", "Day-4 Adaptation (Reg/Integ)", "MAIN_CAMPUS v1 vs RESEARCH_ANNEX v2 limits, expand-and-contract migration + failure restore, /api/v1 vs /api/v2, outbox 3-attempt backoff", "Legacy SQLite DB snapshot + FastAPI TestClient", "100% legacy rows preserved (3 bookings, 2 tickets, 5 audits); v1 & v2 compatible; outbox escalates to Manual Retry Required", "Remove temp DBs"],
        ],
    )

    add_heading_2(doc, "2.2 Boundary, Negative, and Failure-Mode Coverage Analysis")
    add_styled_table(
        doc,
        ["Domain Rule / Interface", "Below Boundary / Valid", "Exact Equality Boundary", "Above Boundary / Invalid", "Negative / Failure Condition"],
        [
            ["Sensor Threshold (MAIN_CAMPUS v1: > 28.0°C)", "27.99°C -> False (U7)", "28.00°C -> False (U6)", "28.01°C -> True (U6)", "Unknown campus_code raises ValueError / HTTP 400"],
            ["Sensor Threshold (RESEARCH_ANNEX v2: > 24.5°C)", "24.49°C -> False", "24.50°C -> False (day4_01)", "24.51°C -> True (day4_01)", "5x & 25x duplicate (source, event_id) replay creates 1 ticket (I2)"],
            ["Booking Duration (MAIN_CAMPUS v1: <= 180m)", "179 min -> True (U8)", "180 min -> True (U8)", "181 min -> False (U8)", "0 min or negative duration -> False (U8)"],
            ["Booking Overlap Window [start, end)", "Non-overlapping 500–580", "Adjacent 600–720 & 720–800 -> Allowed (I4)", "Overlapping 600–720 & 700–800 -> Rejected (I4)", "Missing facility name rejected (HTTP 422/400)"],
            ["UTC SLA Deadline (M1: +1h from 08:00Z)", "08:59:59Z (-1s) -> overdue=False (U9)", "09:00:00Z (0s) -> overdue=False (U9)", "09:00:01Z (+1s) -> overdue=True (U9)", "Invalid priority code raises ValueError"],
            ["Ticket Lifecycle & Optimistic Lock", "Valid sequence with notes (I1)", "expected_version == current_version (I1)", "Stale expected_version=1 when v=2 -> Rejected (R4)", "Resolve with blank notes '   ' -> Rejected (R3); illegal state jump -> Rejected"],
            ["RBAC & External Dependency Outage", "approver/manager/admin -> HTTP 200 (sec_03)", "HMAC signature constant-time match", "student with spoofed {'role':'approver'} -> HTTP 403 (sec_01)", "EXTERNAL_SYNC_FAIL=true -> local HTTP 201, sync_status='Pending', 3 retries -> Manual Retry Required (day4_04)"],
        ],
    )

    add_heading_2(doc, "2.3 Risk-to-Requirement-to-Test-to-Gate Traceability Matrix")
    add_styled_table(
        doc,
        ["Risk ID", "Requirement (FR / NFR)", "Automated Test IDs", "CI/CD Pipeline Release Gate"],
        [
            ["R-01 (Duplicate sensor tickets)", "FR08 Idempotent Sensor Intake", "test_I2, Stage-4 Replay Burst", "Stage 1 Pytest Gate + Unique DB Constraint"],
            ["R-02 (Double booking collision)", "FR05 Booking Duration & Overlap", "test_U8, test_I4, test_day4_03", "Stage 1 Pytest Gate + Stage 2 Smoke Check"],
            ["R-03 (Unauthorized approval / spoofing)", "FR01 / NFR03 Server-Derived RBAC", "test_I3, test_sec_01..04", "Stage 1 Security Suite + Stage 2 Smoke Step 3 (403 check)"],
            ["R-04 (Threshold / SLA off-by-one)", "FR03, FR04, FR07, FR09 Triage & SLA", "test_U1..U7, test_U9..U10, test_R1..R2, test_day4_01", "Stage 1 Pytest Gate (blocks Stage 2 on failure)"],
            ["R-05 (Broken container / startup)", "NFR04 Verified Container Delivery", "test_I5, test_day4_05, scripts/smoke-test.sh", "Stage 2 Docker Compose Readiness + E2E Smoke Gate"],
            ["R-06 (Migration data/audit loss)", "NFR06 Persistence & Schema Evolution", "test_I1, test_day4_02, migrations/002_...", "Stage 1 Migration Rehearsal & Row-Count Parity Gate"],
            ["R-07 (Downstream outage data loss)", "NFR05 Resilient External Sync", "test_I6, test_day4_04", "Stage 1 Outbox Retry Gate + Stage 5 Outage Load Test"],
        ],
    )

    add_heading_2(doc, "2.4 What Remains Outside Automated Coverage & Investigation Plan")
    add_body(
        doc,
        "Automated functional and integration tests verify deterministic rules, SQLite/PostgreSQL persistence, and FastAPI HTTP contracts under synthetic inputs, but they do not establish visual browser accessibility (WCAG keyboard focus, screen-reader semantics), multi-node distributed PostgreSQL lock contention under campus-wide registration spikes, live OAuth2/SAML university SSO federation, or physical IoT MQTT broker packet loss. We investigate these residual areas through: (1) live Chromium browser inspection of the Operations Console UI (Figure 4), (2) a 5-stage bounded concurrent HTTP load and sensor replay experiment (Task 5, Figure 13), and (3) a rehearsed bad-release deployment and database snapshot rollback drill (Task 5, Figure 14).",
    )

    # =========================================================================
    # TASK 3
    # =========================================================================
    add_heading_1(doc, "Task 3 — Implement and Evaluate Automated Tests (12 Marks)")
    add_body(
        doc,
        "We implemented both the compact core domain model (campus_model.py) matching the reference specification and the full FastAPI application (app/main.py, app/auth.py, app/integrations.py). The complete test suite executes 30 automated checks across three test modules: tests/test_model.py (10 unit checks U1–U10, 6 integration checks I1–I6, 5 regression checks R1–R5), tests/test_security_api.py (4 direct API RBAC and anti-spoofing checks), and tests/test_day4_adaptation.py (5 Day-4 policy, migration, API compatibility, and durable outbox checks).",
    )
    add_body(
        doc,
        "python -m pytest tests -v --cov=app --cov=campus_model --cov-report=term-missing --junitxml=evidence/logs/junit-baseline.xml",
        bold_prefix="Exact Execution Command: ",
    )

    add_heading_2(doc, "3.1 Executed Automated Test Results (30 of 30 Passed)")
    add_styled_table(
        doc,
        ["Test ID", "Module & Test Function", "Input / Interaction Verified", "Expected Result", "Observed Status"],
        [
            ["U1", "test_model::test_U1_high_high_is_M1", "priority('High', 'High')", "M1", "PASS"],
            ["U2", "test_model::test_U2_low_low_is_M4", "priority('Low', 'Low')", "M4", "PASS"],
            ["U3", "test_model::test_U3_impact_out_of_range", "priority('Critical', 'High')", "Raises ValueError", "PASS"],
            ["U4", "test_model::test_U4_water_leak_is_facilities", "classify('Water leak from lab ceiling')", "Facilities", "PASS"],
            ["U5", "test_model::test_U5_equal_evidence_manual", "classify('Leak and projector fault')", "Manual Review", "PASS"],
            ["U6", "test_model::test_U6_temperature_threshold", "breached(28.0), breached(28.01)", "(False, True)", "PASS"],
            ["U7", "test_model::test_U7_temperature_below_threshold_boundary", "breached(27.99)", "False", "PASS"],
            ["U8", "test_model::test_U8_booking_duration_boundaries", "valid_duration(0, 179, 180, 181)", "False, True, True, False", "PASS"],
            ["U9", "test_model::test_U9_sla_deadline_and_equality_boundary", "SLA M1 (+1h) at -1s, 0s, +1s", "False, False (on-time), True", "PASS"],
            ["U10", "test_model::test_U10_priority_matrix_all_nine_cells", "All 9 (Impact, Urgency) matrix cells", "Exact M1..M4 mapping", "PASS"],
            ["I1", "test_model::test_I1_commands_persist_and_audit", "File SQLite DB close/reopen after 4 transitions", "State ('Closed', 5), 4 audits", "PASS"],
            ["I2", "test_model::test_I2_repeated_event_one_ticket", "5x identical (sensor-7, evt-1) submissions", "1 unique ticket ID, count==1", "PASS"],
            ["I3", "test_model::test_I3_student_cannot_approve_booking", "approve_booking(b, 'student')", "PermissionError; Pending retained", "PASS"],
            ["I4", "test_model::test_I4_overlap_rejected_adjacent_allowed", "Overlap 700–800 vs adjacent 720–800", "Overlap rejected; adjacent accepted", "PASS"],
            ["I5", "test_model::test_I5_fastapi_end_to_end_booking_ticket_audit_flow", "Full HTTP booking->approve->sensor->4 transitions", "HTTP 201/200; 4 audit rows", "PASS"],
            ["I6", "test_model::test_I6_external_dependency_outage_preserves_local_pending", "POST /api/v1/bookings with EXTERNAL_SYNC_FAIL=true", "HTTP 201; sync_status='Pending'", "PASS"],
            ["R1", "test_model::test_R1_high_medium_is_M2", "priority('High', 'Medium')", "M2", "PASS"],
            ["R2", "test_model::test_R2_unknown_terms_manual", "classify('strange noise somewhere')", "Manual Review", "PASS"],
            ["R3", "test_model::test_R3_resolve_without_notes_rejected", "Transition to Resolved with blank notes '   '", "ValueError; 'In Progress' retained", "PASS"],
            ["R4", "test_model::test_R4_stale_version_rejected", "Transition with stale expected_version=1", "RuntimeError; ('Assigned', 2) retained", "PASS"],
            ["R5", "test_model::test_R5_missing_ticket_title_rejected", "create_ticket('   ')", "ValueError; count==0", "PASS"],
            ["SEC1", "test_security_api::test_sec_01_student_spoofing_approver_in_json_body_rejected", "Student POST approve with {'role':'approver'}", "HTTP 403 Forbidden; Pending retained", "PASS"],
            ["SEC2", "test_security_api::test_sec_02_student_denied_restricted_facilities_and_tickets", "Student GET restricted/tickets/audit & POST transition", "HTTP 403 on all 4 endpoints", "PASS"],
            ["SEC3", "test_security_api::test_sec_03_all_six_roles_permission_matrix", "All 6 roles tested against booking approval API", "admin/manager/approver->200; others->403", "PASS"],
            ["SEC4", "test_security_api::test_sec_04_tampered_or_missing_token_rejected", "Missing header & tampered HMAC signature", "HTTP 401 Unauthorized", "PASS"],
            ["DAY4-1", "test_day4_adaptation::test_day4_01_campus_specific_duration_and_sensor_thresholds", "MAIN_CAMPUS (180m/28.0C) vs RESEARCH_ANNEX (240m/24.5C)", "Exact boundary pass/fail per campus", "PASS"],
            ["DAY4-2", "test_day4_adaptation::test_day4_02_expand_and_contract_migration_preserves_legacy_records", "Rehearse failure restore + full migration on legacy DB", "3 bookings, 2 tickets, 5 audits preserved", "PASS"],
            ["DAY4-3", "test_day4_adaptation::test_day4_03_v1_compatibility_and_v2_campus_policy_api", "200m booking on /api/v1 (400) vs /api/v2 RESEARCH_ANNEX (201)", "v1 compatible; v2 applies policy v2", "PASS"],
            ["DAY4-4", "test_day4_adaptation::test_day4_04_durable_outbox_bounded_retry_and_recovery", "3 failed attempts during outage -> recovery retry", "Pending -> Manual Retry Required -> Synced", "PASS"],
            ["DAY4-5", "test_day4_adaptation::test_day4_05_dashboard_health_ready_and_outbox_endpoints", "GET /health, /ready, /, /api/v2/bookings, /api/v1/outbox", "All return HTTP 200 OK", "PASS"],
        ],
    )

    add_figure(
        doc,
        "01_pytest_baseline_pass.png",
        "Figure 1: Baseline Pytest execution and statement coverage report (30 passed in 2.70s; 82% overall coverage across app/ and campus_model.py).",
    )

    add_heading_2(doc, "3.2 Controlled Defect Injection & Negative-Control Evaluation")
    add_body(
        doc,
        "To verify that our automated test suite actively detects plausible domain regressions rather than producing tautological green results, we injected two controlled defects into campus_model.py, captured the raw failing outputs, restored the correct logic, and confirmed that all checks returned to passing.",
    )
    add_styled_table(
        doc,
        ["Controlled Defect", "Exact Code Mutation in campus_model.py", "Observed Failing Test(s) & Assertion Output", "Correction & Retest Result"],
        [
            [
                "Defect 1: Sensor Threshold Off-by-One Boundary Bug",
                "Changed strict comparison `return value > limit` to inclusive `return value >= limit` in `breached()` (line 146).",
                "FAILED tests/test_model.py::test_U6_temperature_threshold — `AssertionError: assert (True, True) == (False, True)` (28.0°C falsely breached; 1 failed, 20 passed in 1.05s).",
                "Restored strict `return value > limit`; re-ran pytest: 21 of 21 in test_model.py (30 of 30 total) PASSED in 0.90s.",
            ],
            [
                "Defect 2: Priority Matrix Critical Triage Bug",
                "Changed `('High', 'High'): 'M1'` to `('High', 'High'): 'M2'` in `MATRIX` (line 9).",
                "FAILED tests/test_model.py::test_U1_high_high_is_M1 and test_U10_priority_matrix_all_nine_cells — `AssertionError: assert 'M2' == 'M1'` (2 failed, 19 passed in 1.10s).",
                "Restored `('High', 'High'): 'M1'` in `MATRIX`; re-ran pytest: 21 of 21 in test_model.py (30 of 30 total) PASSED.",
            ],
        ],
    )

    add_figure(
        doc,
        "02_defect1_threshold_fail.png",
        "Figure 2: Controlled Defect 1 execution — replacing `>` with `>=` in `breached()` causes `test_U6_temperature_threshold` to fail at the exact 28.0°C equality boundary.",
    )
    add_figure(
        doc,
        "03_defect2_priority_fail.png",
        "Figure 3: Controlled Defect 2 execution — mutating `('High', 'High')` from `M1` to `M2` is immediately caught by `test_U1_high_high_is_M1` and `test_U10_priority_matrix_all_nine_cells`.",
    )

    add_heading_2(doc, "3.3 Coverage Interpretation & Why Passing Tests Do Not Prove Defect Absence")
    add_body(
        doc,
        "The baseline run achieved 82% total statement coverage across 472 executable statements (campus_model.py: 89%, app/integrations.py: 95%, app/auth.py: 84%, app/main.py: 74%, where uncovered lines in main.py are primarily the HTML log-viewer helper routes). As Dijkstra established, testing can demonstrate the presence of defects but never their absence. Passing all 30 checks proves only that the implemented code satisfies the tested assertions for the discrete inputs we selected. It does not prove absence of defects for: (1) unrepresented vocabulary not present in KEYWORDS, (2) multi-thread connection contention under concurrent HTTP load (which we only discovered when running the 50-client bounded load experiment in Task 5), or (3) environment differences between local Windows and Linux containers (which we discovered when a Ruff configuration disparity failed Run #44576532661 on GitHub Actions).",
    )

    # =========================================================================
    # TASK 4
    # =========================================================================
    add_heading_1(doc, "Task 4 — Construct a DevOps Delivery Pipeline (8 Marks)")
    add_body(
        doc,
        "We constructed a two-stage gated CI/CD pipeline in `.github/workflows/ci.yml` triggered on every `push` and `pull_request`, backed by a hardened multi-stage `Dockerfile`, an isolated `docker-compose.yml` stack (`postgres:16-alpine` + `campus-api`), and an automated post-deployment smoke verification script (`scripts/smoke-test.sh` invoking `scripts/smoke_test.py`).",
    )

    add_heading_2(doc, "4.1 Staged Pipeline Architecture & Quality Gates")
    add_styled_table(
        doc,
        ["Stage & Job ID", "Executed Steps & Security Scans", "Failure Gate Behaviour", "Published Artifacts & Identifiers"],
        [
            [
                "Stage 1: test-and-security (ubuntu-latest + postgres:16-alpine service)",
                "1. actions/checkout@v4 & Python 3.12 setup with pip cache\n2. Static linting: ruff check (--config pyproject.toml)\n3. Secret scan: python scripts/secret_scan.py\n4. Day-4 Migration & Restore Gate: migrations/002_campus_policies_and_outbox.py --seed-legacy --rehearse-failure\n5. SAST scan: bandit -r app campus_model.py -ll\n6. Dependency audit: pip-audit\n7. Automated test suite: pytest tests -v --cov=app --cov=campus_model --junitxml=test-results.xml",
                "Any non-zero exit code immediately aborts Stage 1 and prevents Stage 2 from starting (`needs: test-and-security`).",
                "Uploads `test-and-security-reports-${{ github.sha }}` (`test-results.xml`, `coverage.xml`, `bandit-report.txt`) via `if: always()` even when tests fail.",
            ],
            [
                "Stage 2: build-deploy-smoke (needs: test-and-security)",
                "1. Multi-stage Docker build: `docker build -t campus-backend:${{ github.sha }}`\n2. Record immutable Docker Image SHA256 Digest (`docker inspect`)\n3. Container vulnerability scan: `aquasecurity/trivy-action@master` (OS & library packages, HIGH/CRITICAL)\n4. Isolated deployment: `docker compose up -d`\n5. Authenticated E2E smoke journey: `./scripts/smoke-test.sh http://127.0.0.1:8000`\n6. Rehearsed failure & rollback drill: `python scripts/recovery_rehearsal.py`\n7. Teardown: `docker compose down -v` (`if: always()`)",
                "Skipped automatically if Stage 1 fails. Fails release if `/ready` or any step of the authenticated create-approve-sensor-transition-audit smoke journey fails.",
                "Immutable container tag `campus-backend:${{ github.sha }}` and SHA256 image digest printed in runner logs.",
            ],
        ],
    )

    add_heading_2(doc, "4.2 Secrets Management, Security Scanning Scope & Traceable Release Artifacts")
    add_body(
        doc,
        "Zero secrets are hardcoded in source files. Repository credentials (`APP_SECRET_KEY` for HMAC-SHA256 token signing and `TEST_DB_PASSWORD` for the isolated PostgreSQL 16 service container) are stored in GitHub Actions Encrypted Secrets (Figure 6) and injected at runtime as environment variables. Local development uses `.env.example` (committed template) and `.env` (excluded via `.gitignore`). Security scanning operates at four layers: (1) `scripts/secret_scan.py` checks all Python files for AWS keys, GitHub PATs, and PEM private keys; (2) `Bandit` performs AST static analysis (`-ll` Medium/High severity threshold, 0 issues found across 1,056 lines of code); (3) `pip-audit` checks Python dependencies against the OSV advisory database; and (4) `Trivy` scans the built Debian/Python container filesystem for unfixed HIGH/CRITICAL CVEs.",
    )
    add_styled_table(
        doc,
        ["Release Artifact / Run Attribute", "Observed Value from Live Execution"],
        [
            ["GitHub Repository", "https://github.com/saikeerthan006-commits/smart-campus-facility-devops"],
            ["Passing Release Commit SHA (main)", "201117de779cf011da5dcb4353979d3c8de0b7d7 (short: 201117d)"],
            ["Passing GitHub Actions Run ID & URL", "Run #44577255849 — https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577255849"],
            ["Docker Image Version Tag", "campus-backend:201117de779cf011da5dcb4353979d3c8de0b7d7"],
            ["Docker Image SHA256 Digest", "sha256:e4d522ba641e7c06d004e4122ce7e690f107fec3ef07a378ac0942b853890611"],
            ["Uploaded CI Evidence Bundle", "test-and-security-reports-201117de779cf011da5dcb4353979d3c8de0b7d7 (test-results.xml, coverage.xml, bandit-report.txt)"],
            ["Blocked Defective Branch & Commit SHA", "demo/defect-threshold-gate — 2f3e4a8bfd64362515f14906d74e99c209439051 (short: 2f3e4a8)"],
            ["Blocked GitHub Actions Run ID & URL", "Run #44577269915 — https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577269915"],
            ["Blocked Pull Request URL & Final State", "PR #1 (https://github.com/saikeerthan006-commits/smart-campus-facility-devops/pull/1) — Blocked by Stage 1 gate & Closed without merge"],
        ],
    )

    add_code_block(
        doc,
        "Key Excerpt — .github/workflows/ci.yml (Two-Stage Gated Pipeline):",
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"),
    )
    add_code_block(
        doc,
        "Key Excerpt — Multi-Stage Production Dockerfile (Non-Root Runtime):",
        (ROOT / "Dockerfile").read_text(encoding="utf-8"),
    )

    add_figure(
        doc,
        "04_live_app_ui.png",
        "Figure 4: Live deployed Smart Campus Facility & Maintenance Platform Operations Console UI (http://localhost:8000) displaying active v1/v2 bookings, versioned campus policies, immutable ticket transition audits, and durable outbox sync state.",
    )
    add_figure(
        doc,
        "05_docker_smoke_pass.png",
        "Figure 5: Post-deployment end-to-end smoke verification (`./scripts/smoke-test.sh http://127.0.0.1:8000`) verifying `/ready`, booking creation, student 403 anti-spoofing rejection, booking approval, sensor idempotency, and 4 ticket audit transitions.",
    )
    add_figure(
        doc,
        "06_github_secrets.png",
        "Figure 6: GitHub Actions Repository Secrets configuration showing `APP_SECRET_KEY` and `TEST_DB_PASSWORD` stored outside source code.",
    )
    add_figure(
        doc,
        "07_gha_success_overview.png",
        "Figure 7: Passing GitHub Actions workflow run summary (Run #44577255849, commit 201117d on `main`) showing both Stage 1 (37s) and Stage 2 (1m 12s) green with 1 published evidence artifact.",
    )
    add_figure(
        doc,
        "08_gha_success_logs.png",
        "Figure 8: Expanded Stage 2 runner logs from Run #44577255849 showing multi-stage Docker image build (`campus-backend:201117de779cf011da5dcb4353979d3c8de0b7d7`), exact SHA256 digest (`sha256:e4d522ba641e...`), Trivy container scan, and isolated Docker Compose smoke deployment.",
    )
    add_figure(
        doc,
        "09_gha_blocked_overview.png",
        "Figure 9: Blocked GitHub Actions workflow run summary (Run #44577269915, commit 2f3e4a8 on `demo/defect-threshold-gate`) showing Stage 1 failed (red X), Stage 2 automatically skipped/blocked, and failure diagnostic artifact uploaded.",
    )
    add_figure(
        doc,
        "10_gha_blocked_log.png",
        "Figure 10: Expanded Stage 1 failure log from Run #44577269915 showing `FAILED tests/test_model.py::test_U6_temperature_threshold` (`assert (True, True) == (False, True)`) halting the pipeline before container packaging.",
    )
    add_figure(
        doc,
        "11_github_pr_blocked.png",
        "Figure 11: Pull Request #1 (`demo/defect-threshold-gate` -> `main`) status checks showing `Stage 1: Automated Tests, Security & Migration Gate` failing and `Stage 2` skipped, preventing merge of the defective release.",
    )

    # =========================================================================
    # TASK 5
    # =========================================================================
    add_heading_1(doc, "Task 5 — Validate Reliability, Security and Recovery (6 Marks)")

    add_heading_2(doc, "5.1 Direct API Security, RBAC Matrix & Anti-Spoofing Validation")
    add_body(
        doc,
        "Because UI controls can be bypassed by direct HTTP clients (`curl`, `httpx`, Postman), `app/auth.py` enforces authentication and role authorization directly on every FastAPI route via `Depends(get_current_actor)`. The server parses the `Authorization: Bearer <token>` header, verifies the HMAC-SHA256 signature in constant time (`hmac.compare_digest`), and extracts the actor's role exclusively from the signed token payload. Any `"
        "role` attribute injected into a JSON request body (e.g., `{\"role\": \"approver\"}`) is ignored. We validated all 6 platform roles directly against the API (`tests/test_security_api.py`):",
    )
    add_styled_table(
        doc,
        ["Role Identity (Bearer Token)", "POST /api/v1/bookings (Create)", "POST /api/v1/bookings/{id}/approve (with spoofed body role='admin')", "POST /api/v1/tickets/{id}/transition", "GET /api/v1/facilities/restricted & /api/v1/tickets"],
        [
            ["admin", "201 Created", "200 OK (Status -> Approved)", "200 OK (State transitioned + Audit row)", "200 OK"],
            ["manager", "201 Created", "200 OK (Status -> Approved)", "200 OK (State transitioned + Audit row)", "200 OK"],
            ["approver", "201 Created", "200 OK (Status -> Approved)", "403 Forbidden (State & Audit unchanged)", "200 OK"],
            ["technician", "201 Created", "403 Forbidden (Remains Pending)", "200 OK (State transitioned + Audit row)", "200 OK"],
            ["faculty", "201 Created", "403 Forbidden (Remains Pending)", "403 Forbidden (State & Audit unchanged)", "200 OK"],
            ["student", "201 Created", "403 Forbidden (Remains Pending; spoof ignored)", "403 Forbidden (State & Audit unchanged)", "403 Forbidden (Denied access)"],
        ],
    )

    add_figure(
        doc,
        "12_security_rbac_test.png",
        "Figure 12: Direct API security validation (`tests/test_security_api.py`) confirming student role-spoofing rejection (HTTP 403), restricted endpoint protection, 6-role matrix enforcement, and tampered HMAC signature rejection (HTTP 401).",
    )

    add_heading_2(doc, "5.2 Actual Bounded Load, Sensor Replay Burst & Dependency Outage Experiment")
    add_body(
        doc,
        "We executed a five-stage bounded load experiment (`python loadtest/run_bounded_load.py`) against a live local Uvicorn/FastAPI server instance (`http://127.0.0.1:8091`) on a Windows 11 host (`10.0.26200`, Python `3.13.9`, `16` logical CPU cores, file-backed SQLite database). Notably, our initial unserialized multi-threaded run at 25–50 clients exposed a real concurrency defect (`sqlite3.InterfaceError: bad parameter or other API misuse` when FastAPI's threadpool worker threads shared a single `sqlite3.Connection` concurrently). We resolved this by implementing `_ThreadSafeConnection` with a re-entrant lock (`threading.RLock`) and atomic `INSERT OR IGNORE` idempotency in `campus_model.py`, eliminating all 5xx errors across all five stages:",
    )
    add_styled_table(
        doc,
        ["Experiment Stage & Condition", "Concurrency & Workload", "Duration (s)", "Throughput (RPS)", "p50 Latency", "p95 Latency", "p99 Latency", "5xx Errors", "Observed Persistence & Outbox State"],
        [
            [
                "Stage 1: Baseline Mixed Workload",
                "10 concurrent clients (120 requests: 25% /ready, 25% POST v2 booking, 25% POST ticket, 25% GET bookings)",
                "0.619 s",
                "193.84 req/s",
                "47.79 ms",
                "91.07 ms",
                "132.30 ms",
                "0",
                "All 120 requests succeeded; 0 lock timeouts.",
            ],
            [
                "Stage 2: Medium Concurrency",
                "25 concurrent clients (250 mixed requests)",
                "1.434 s",
                "174.33 req/s",
                "127.87 ms",
                "288.78 ms",
                "337.97 ms",
                "0",
                "All 250 requests succeeded; p95 < 300 ms.",
            ],
            [
                "Stage 3: Peak Bounded Concurrency",
                "50 concurrent clients (400 mixed requests)",
                "3.442 s",
                "116.21 req/s",
                "360.47 ms",
                "825.99 ms",
                "993.35 ms",
                "0",
                "All 400 requests succeeded; serialized write queue increases p95 to 825.99 ms.",
            ],
            [
                "Stage 4: Sensor Replay Burst",
                "50 concurrent sensor breach POSTs (25 duplicate retries of `evt-burst-dup` + 25 unique event IDs)",
                "0.498 s",
                "100.38 req/s",
                "363.06 ms",
                "470.82 ms",
                "476.89 ms",
                "0",
                "Exactly 26 new tickets created (1 from 25 duplicates + 25 unique); 0 duplicate leaks.",
            ],
            [
                "Stage 5: Dependency Unavailable Mode",
                "15 concurrent clients (90 mixed requests) with `EXTERNAL_SYNC_FAIL=true`",
                "0.770 s",
                "116.81 req/s",
                "111.71 ms",
                "212.44 ms",
                "263.94 ms",
                "0",
                "100% of local bookings/tickets saved; 46 outbox records queued as `Pending` (0 falsely marked `Synced`).",
            ],
        ],
    )
    add_body(
        doc,
        "Because this experiment ran on a single host machine with both the async load generator and the Uvicorn server sharing 16 CPU cores and a serialized SQLite file lock (`_ThreadSafeConnection`), p95 latency rose from 91.07 ms (10 clients) to 825.99 ms (50 clients). These results validate single-node bounded concurrency and idempotency under burst retries, but do not measure multi-node network latency or PostgreSQL connection-pool scaling across separate physical servers.",
        bold_prefix="Reported Load Limitations: ",
    )

    add_figure(
        doc,
        "13_bounded_load_results.png",
        "Figure 13: Live Bounded Load & Outage Telemetry Report (`http://localhost:8000/load-report`) showing 10, 25, and 50 client concurrency stages, the 50-event sensor replay burst (26/26 exact tickets), and the dependency outage stage (46 Pending outbox intents).",
    )

    add_heading_2(doc, "5.3 Rehearsed Release Failure, Database Backup & Rollback Recovery")
    add_body(
        doc,
        "We executed a complete five-step failure and recovery rehearsal (`python scripts/recovery_rehearsal.py`) both locally and inside Stage 2 of our GitHub Actions pipeline. A critical engineering distinction governs stateful rollback: a Docker named volume (`campus_data:/app/data`) provides container-restart persistence, NOT a backup, because any corrupting write or destructive schema change inside the container mutates the volume in place. Similarly, rolling back a container image tag/digest alone does not reverse a database mutation. Therefore, our release procedure captures a verified off-volume database snapshot (`pre_release_v1.sql` and `pre_release_v1.db`) with SHA-256 checksums prior to every deployment:",
    )
    add_styled_table(
        doc,
        ["Rehearsal Step", "Executed Action & Command", "Observed Verification Evidence & Metrics"],
        [
            [
                "Step A: Deploy Healthy Release v1.0.0",
                "Deploy `APP_VERSION=v1.0.0`, record release digest, probe `GET /ready`.",
                "Release Digest: `sha256:ea9b953db516cad73380a6e6d83cb503cc788084c6c0f41eb6f4d33037e87d33`; `/ready` returned HTTP 200 OK.",
            ],
            [
                "Step B: Seed Operational Records",
                "Create Booking #1 (`Lab-204`, MAIN_CAMPUS v1) and approve it; create Booking #2 (`Cryo-Annex-01`, RESEARCH_ANNEX v2); ingest sensor breach Ticket #1 and transition through 3 audit states to `Resolved` (v4).",
                "Recorded Pre-Release Row Counts: `{'bookings': 2, 'tickets': 1, 'audit': 3, 'policies': 2, 'integration_outbox': 3}`.",
            ],
            [
                "Step C: Execute & Verify Off-Volume Backup",
                "Execute SQLite `.iterdump()` to `evidence/backups/pre_release_v1.sql` and binary `.backup()` to `pre_release_v1.db`; compute SHA-256 digests.",
                "`pre_release_v1.sql` (3,510 bytes, `sha256:acf3c67c16e24142b3139548...`); `pre_release_v1.db` (36,864 bytes, `sha256:192c7d514bf56323c5916494...`).",
            ],
            [
                "Step D: Deploy Faulty Release v2.0.0-broken & Detect Failure",
                "Deploy `APP_VERSION=v2.0.0-broken` (`SIMULATE_BROKEN_RELEASE=true`) and execute automated smoke readiness probes.",
                "`/health` returned HTTP 500; `/ready` returned HTTP 503 (`Simulated broken release readiness gate failure`). Smoke gate aborted release automatically.",
            ],
            [
                "Step E: Timed Rollback & Snapshot Restoration",
                "Restore verified snapshot `pre_release_v1.db`, revert release to `v1.0.0` digest, re-verify `/ready` and query all tables and individual record states.",
                "`/ready` HTTP 200 OK; Post-Rollback Row Counts `{'bookings': 2, 'tickets': 1, 'audit': 3, 'policies': 2, 'integration_outbox': 3}` (0 records lost); Booking #1=`Approved`, Ticket #1=`('Resolved', 4)`; Total Measured Recovery Time (RTO) = **0.0095 seconds**.",
            ],
        ],
    )

    add_figure(
        doc,
        "14_recovery_rollback.png",
        "Figure 14: Executed 5-step failure detection, off-volume backup checksum verification, and rollback recovery transcript (`scripts/recovery_rehearsal.py`) achieving 100% data retention in 0.0095 seconds.",
    )

    # =========================================================================
    # TASK 6
    # =========================================================================
    add_heading_1(doc, "Task 6 — Adapt the Tests and Pipeline to a Changed Release (Day-4 Challenge, 8 Marks)")

    add_heading_2(doc, "6.1 Part A — Impact Diagnosis Across Rules, Interfaces, Data, Tests & Assumptions")
    add_styled_table(
        doc,
        ["System Layer", "Pre-Change Baseline Assumption", "Day-4 Changed Requirement Impact", "Required Engineering Adaptation"],
        [
            [
                "Domain Rules (campus_model.py)",
                "Single global `MAX_MINUTES = 180` and `TEMP_LIMIT = 28.0` applied to all bookings and sensor alerts.",
                "Different campuses require distinct duration and temperature limits (e.g., research labs need longer slots and stricter cooling thresholds).",
                "Introduce versioned `CAMPUS_POLICIES` registry & `policies` table: `MAIN_CAMPUS` (`v1`: 180m, 28.0°C) and `RESEARCH_ANNEX` (`v2`: 240m, 24.5°C). Parameterize `breached()` and `valid_duration()` by `campus_code`.",
            ],
            [
                "HTTP API Interfaces (app/main.py)",
                "Single `/api/v1/bookings` endpoint without campus selection or policy metadata in response.",
                "New clients require campus-aware booking creation, but existing legacy v1 clients must not break during the transition.",
                "Add `/api/v2/bookings` accepting `campus_code` and returning `policy_version`, `max_duration_allowed`, and `sync_status`. Retain `/api/v1/bookings` as a backward-compatible adapter defaulting to `MAIN_CAMPUS` / `v1`.",
            ],
            [
                "Stored Database Schema & Historical Data",
                "`bookings` and `tickets` tables lacked `campus_code`, `policy_version`, and `sync_status`; no `policies` or `integration_outbox` tables existed.",
                "In-place destructive `DROP/CREATE` would wipe existing approved bookings, active maintenance tickets, and immutable audit history.",
                "Implement staged Expand-and-Contract migration (`migrations/002_campus_policies_and_outbox.py`): add nullable/defaulted columns, backfill legacy rows with `MAIN_CAMPUS` / `v1`, and assert exact row-count parity.",
            ],
            [
                "External Calendar & Issue-Tracker Sync",
                "Synchronous assumption that downstream calendar and issue-tracker services are always reachable.",
                "Downstream calendar and issue-tracker services become intermittently unavailable; local work must never be lost or falsely reported as `Synced`.",
                "Implement durable `integration_outbox` table (`app/integrations.py`) with unique `idempotency_key`, bounded exponential backoff (`max_attempts=3`), and escalation to `Manual Retry Required`.",
            ],
            [
                "Automated Tests & CI/CD Release Gates",
                "Pipeline only ran unit/integration tests against fresh schema; no migration rehearsal gate existed.",
                "A broken migration script could corrupt production records even if fresh-schema unit tests pass.",
                "Add `tests/test_day4_adaptation.py` (5 checks) and add a mandatory Stage 1 migration rehearsal gate (`--seed-legacy --rehearse-failure`) before pytest and Docker packaging.",
            ],
        ],
    )

    add_heading_2(doc, "6.2 Part B — Adaptation Design: Versioned Policies, Expand-and-Contract Migration & Durable Outbox")
    add_body(
        doc,
        "1. Expand-and-Contract Migration Procedure: In Phase 1 (Expand), `migrations/002_campus_policies_and_outbox.py` takes a point-in-time file backup (`.pre_day4.bak`), inspects `PRAGMA table_info`, and adds `campus_code`, `policy_version`, `sync_status`, and `created_at` columns with safe defaults alongside the new `policies` and `integration_outbox` tables. In Phase 2 (Backfill & Verify), existing historical rows are populated with `MAIN_CAMPUS` and `policy_version='v1'` so historical bookings and tickets continue to be evaluated under the policy active when they were created. In Phase 3 (Verify Gate), the script asserts `pre_counts == post_counts` across `bookings`, `tickets`, and `audit`; if any count mismatches or an error occurs, the transaction aborts and automatically restores the `.pre_day4.bak` snapshot.",
    )
    add_body(
        doc,
        "2. Safe Dependency-Failure & Durable Outbox Design: Every booking creation and ticket/sensor ingestion writes a durable intent row into `integration_outbox` (`idempotency_key = cal-booking-{id}` or `issue-sensor-{source}-{event_id}`) inside the local database before attempting external synchronization. When `EXTERNAL_SYNC_FAIL=true` (or a timeout occurs), the local booking or ticket transaction still succeeds (HTTP 201/200), while its `sync_status` is explicitly recorded as `Pending`—never falsely displayed as `Synced`. Each retry increments `attempts` and schedules `next_retry_at = now + 2^attempts` seconds. Upon reaching `MAX_RETRY_ATTEMPTS = 3`, the outbox record transitions to `Manual Retry Required` with the exact error reason visible on the Operations Console (Figure 4). Once connectivity is restored, invoking `POST /api/v1/outbox/{idempotency_key}/retry` completes synchronization, records the confirmed remote identifier (`ISSUE-TRACKER-TICKET-1`), and updates `sync_status` to `Synced`.",
    )

    add_code_block(
        doc,
        "Key Excerpt — migrations/002_campus_policies_and_outbox.py (Expand-and-Contract & Auto-Restore):",
        (ROOT / "migrations" / "002_campus_policies_and_outbox.py").read_text(encoding="utf-8"),
    )

    add_heading_2(doc, "6.3 Part C — Executed Migration Validation, Controlled Failure Recovery & Release Defence")
    add_styled_table(
        doc,
        ["Day-4 Validation Check", "Executed Procedure", "Observed Result & Evidence"],
        [
            [
                "Controlled Migration Failure & Auto-Restore Rehearsal",
                "`run_expand_and_contract_migration(db, simulate_failure=True)` triggered mid-migration invariant abort.",
                "Status: `MIGRATION_ABORTED_AND_RESTORED`; pre-migration backup `.pre_day4.bak` automatically restored; verified `pre_counts == restored_counts == {'bookings': 3, 'tickets': 2, 'audit': 5}` (0 data loss).",
            ],
            [
                "Full Expand-and-Contract Migration Execution",
                "`run_expand_and_contract_migration(db, simulate_failure=False)` on seeded legacy v1 database.",
                "Status: `MIGRATION_SUCCESS`; `post_counts == {'bookings': 3, 'tickets': 2, 'audit': 5, 'policies': 2}`. All 3 legacy bookings accessible via `/api/v1/bookings` with `campus_code='MAIN_CAMPUS'` and `policy_version='v1'`.",
            ],
            [
                "Backward-Compatible v1 vs Campus-Specific v2 API",
                "`test_day4_03`: Submit 200-minute booking to `/api/v1/bookings` and `/api/v2/bookings` (`RESEARCH_ANNEX`).",
                "`/api/v1/bookings` rejected 200m slot with HTTP 400 (enforcing MAIN_CAMPUS 180m v1 limit); `/api/v2/bookings` accepted 200m slot with HTTP 201 under `RESEARCH_ANNEX` `v2` (240m limit).",
            ],
            [
                "Durable Outbox Bounded Retry & Recovery",
                "`test_day4_04`: Ingest 25.0°C sensor breach in `RESEARCH_ANNEX` (> 24.5°C v2 limit) during outage, retry to attempt 3, then recover.",
                "Attempt 1 & 2: `status='Pending'`; Attempt 3: escalated to `Manual Retry Required` (`attempts=3`); Post-outage retry: `status='Synced'`, `remote_id='ISSUE-TRACKER-TICKET-1'`.",
            ],
        ],
    )

    add_figure(
        doc,
        "15_day4_migration_and_tests.png",
        "Figure 15: Executed Day-4 Expand-and-Contract migration rehearsal (showing controlled failure auto-restore and full migration row-count parity: 3 bookings, 2 tickets, 5 audits) followed by all 5 Day-4 adaptation tests passing.",
    )
    add_figure(
        doc,
        "16_day4_gha_pipeline_pass.png",
        "Figure 16: Live GitHub Actions Stage 1 execution log (Run #44577255849) showing the Day-4 Migration & Failure Restore Gate (`MIGRATION_SUCCESS`) and all 30 automated unit, integration, security, and Day-4 regression tests passing in CI.",
    )

    add_body(
        doc,
        "Retaining `/api/v1/bookings` alongside `/api/v2/bookings` and keeping nullable/defaulted columns during the Expand phase slightly increases maintenance overhead and schema width, but eliminates flag-day client outages and permits zero-downtime rollback. Residual risks include: (1) hidden legacy consumers that hardcode 180-minute assumptions when querying `/api/v1/bookings` for rows created via `/api/v2/bookings` on `RESEARCH_ANNEX`, and (2) background outbox retry accumulation if an external calendar outage persists beyond 72 hours. We recommend a **Conditional-Go Release Decision**: the release is approved for deployment because all 30 automated checks, the migration row-count parity gate, the RBAC security matrix, the 50-client bounded load test, and the Docker Compose smoke journey passed in Run `#44577255849`, subject to configuring an operational alert whenever `integration_outbox` rows in `Manual Retry Required` state exceed 10.",
        bold_prefix="Trade-Offs, Residual Risks & Release Decision (Conditional-Go): ",
    )

    # =========================================================================
    # TASK 7
    # =========================================================================
    add_heading_1(doc, "Task 7 — Individual Technical Reflection (4 Marks)")
    add_body(
        doc,
        "In our unit and regression suite, `test_U6_temperature_threshold` (paired with `test_day4_01_campus_specific_duration_and_sensor_thresholds`) exposed the most consequential logic defect during Controlled Defect 1 (changing `>` to `>=` in `breached()`, commit `2f3e4a8`). Because HVAC sensors routinely hover at the nominal setpoint of `28.00°C` (`MAIN_CAMPUS`) or `24.50°C` (`RESEARCH_ANNEX`), an inclusive `>=` comparison triggers continuous false-positive maintenance dispatches at normal operating temperature. Even more revealingly, during our Task 5 bounded load experiment (`loadtest/run_bounded_load.py`), driving 25 to 50 concurrent synthetic HTTP clients against the live FastAPI service exposed an application-level concurrency defect (`sqlite3.InterfaceError: bad parameter or other API misuse` and a check-then-insert race on `integration_outbox.idempotency_key`) that single-threaded `TestClient` checks could not trigger. Fixing this required introducing `_ThreadSafeConnection` (`threading.RLock`) and atomic `INSERT OR IGNORE` statements in `campus_model.py` and `app/integrations.py`.",
        bold_prefix="1. Which Test Exposed the Most Consequential Defect: ",
    )
    add_body(
        doc,
        "The combination of the Stage 1 automated Pytest + Migration Parity Gate (`test-and-security`) and the Stage 2 Docker Compose End-to-End Smoke Gate (`scripts/smoke-test.sh` in `build-deploy-smoke`) provided the strongest release evidence. In blocked GitHub Actions Run `#44577269915` (commit `2f3e4a8` on PR #1), Stage 1 caught the `test_U6_temperature_threshold` failure in 33 seconds, uploaded `test-results.xml`, and automatically skipped Stage 2 container packaging and deployment. In passing Run `#44577255849` (commit `201117d`), Stage 2 proved that the packaged non-root container (`sha256:e4d522ba641e7c06d004e4122ce7e690f107fec3ef07a378ac0942b853890611`) started cleanly, enforced HTTP 403 against a student role-spoofing payload, and persisted 4 ticket transitions in an isolated environment. However, these gates could not establish multi-node PostgreSQL lock scalability, external OAuth2/SSO token revocation latency, or visual UI usability.",
        bold_prefix="2. Strongest Release Gate & What It Could Not Establish: ",
    )
    add_body(
        doc,
        "Two real observed failures directly changed our pipeline and code: First, when we pushed commit `2d836b5` (Run `#44575139078`) and commit `3107aa8` (Run `#44576532661`) to GitHub Actions, Stage 1 failed before reaching Pytest—first due to an inline multiline `python -c` YAML indentation error and Windows CRLF line endings on `smoke-test.sh`, and second because the Ubuntu runner's default Ruff rule configuration flagged import-ordering after `sys.path.insert` that had been ignored by our local parent configuration. We revised the pipeline by extracting `scripts/secret_scan.py`, adding `.gitattributes` (`* text=auto eol=lf`), and committing an explicit `pyproject.toml`, which made Run `#44577255849` deterministic across Windows and Linux. Second, our Day-4 migration failure on `ALTER TABLE ... ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP` (rejected by SQLite during `test_day4_02`) forced us to use constant ISO-8601 defaults in `migrations/002_campus_policies_and_outbox.py` and keep the `--rehearse-failure` gate mandatory in Stage 1.",
        bold_prefix="3. How Observed Failures Changed Our Pipeline and Strategy: ",
    )
    add_body(
        doc,
        "Before a live campus production release, the most critical remaining risk is single-connection SQLite write serialization (`p95 = 825.99 ms` at 50 concurrent clients) and in-process outbox retry scheduling. Before production cutover, the SQLAlchemy/PostgreSQL pooled driver against the `postgres:16-alpine` service should replace the single-file SQLite store for concurrent write transactions, and an asynchronous background worker (with dead-letter alerting on `Manual Retry Required` rows) should drain `integration_outbox` independently of request threads.",
        bold_prefix="4. Most Important Remaining Risk Before Production Release: ",
    )

    # =========================================================================
    # APPENDIX
    # =========================================================================
    add_heading_1(doc, "Appendix — Reproducible Source Listings, Raw Defect Logs & Commands")

    add_heading_2(doc, "A.1 Exact Copy-Paste Reproduction Commands")
    repro_cmds = """# 1. Clone the repository and install dependencies
git clone https://github.com/saikeerthan006-commits/smart-campus-facility-devops.git
cd smart-campus-facility-devops
pip install -r requirements.txt

# 2. Run static lint, secret scan, and SAST security check
ruff check app campus_model.py tests migrations scripts loadtest
python scripts/secret_scan.py
bandit -r app campus_model.py -ll

# 3. Execute all 30 automated unit, integration, security & Day-4 regression tests with coverage
python -m pytest tests -v -W ignore --cov=app --cov=campus_model --cov-report=term-missing --junitxml=evidence/logs/junit-baseline.xml

# 4. Run Day-4 Expand-and-Contract database migration rehearsal (including controlled failure & restore)
python migrations/002_campus_policies_and_outbox.py --seed-legacy --rehearse-failure

# 5. Run 5-stage bounded concurrent load, sensor replay burst & dependency outage experiment
python loadtest/run_bounded_load.py

# 6. Run 5-step release failure detection, off-volume backup checksum & rollback recovery rehearsal
python scripts/recovery_rehearsal.py

# 7. Build and deploy isolated container stack via Docker Compose and execute end-to-end smoke check
docker compose up -d --build
./scripts/smoke-test.sh http://127.0.0.1:8000
docker compose down -v"""
    add_code_block(doc, "Reproducible CLI Execution Sequence:", repro_cmds)

    add_heading_2(doc, "A.2 Complete Core Domain Model Listing (campus_model.py)")
    add_code_block(
        doc,
        "File 1: campus_model.py",
        (ROOT / "campus_model.py").read_text(encoding="utf-8"),
    )

    add_heading_2(doc, "A.3 Complete Unit, Integration & Regression Test Listing (tests/test_model.py)")
    add_code_block(
        doc,
        "File 2: tests/test_model.py",
        (ROOT / "tests" / "test_model.py").read_text(encoding="utf-8"),
    )

    add_heading_2(doc, "A.4 Raw Failing Output for Controlled Defect 1 and Controlled Defect 2")
    d1_raw = (LOGS / "defect1_fail.txt").read_text(encoding="utf-8", errors="replace")
    d2_raw = (LOGS / "defect2_fail.txt").read_text(encoding="utf-8", errors="replace")
    add_code_block(
        doc,
        "Raw Failing Pytest Output — Controlled Defect 1 (`>=` instead of `>` in sensor threshold):",
        "\n".join(d1_raw.splitlines()[-28:]),
    )
    add_code_block(
        doc,
        "Raw Failing Pytest Output — Controlled Defect 2 (`('High', 'High')` returns `'M2'` instead of `'M1'`):",
        "\n".join(d2_raw.splitlines()[-28:]),
    )

    add_heading_2(doc, "A.5 Raw Rehearsed Recovery & Bounded Load Logs")
    add_code_block(
        doc,
        "Raw Transcript — scripts/recovery_rehearsal.py (evidence/logs/recovery_rehearsal.txt):",
        (LOGS / "recovery_rehearsal.txt").read_text(encoding="utf-8", errors="replace"),
    )
    add_code_block(
        doc,
        "Raw Transcript — loadtest/run_bounded_load.py (evidence/logs/load_test_results.txt):",
        (LOGS / "load_test_results.txt").read_text(encoding="utf-8", errors="replace"),
    )

    add_heading_2(doc, "A.6 Live GitHub Repository, Actions Runs & Acknowledgements")
    add_body(
        doc,
        "• GitHub Repository: https://github.com/saikeerthan006-commits/smart-campus-facility-devops\n"
        "• Passing CI/CD Run (#44577255849, commit 201117d): https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577255849\n"
        "• Blocked Defective Run (#44577269915, commit 2f3e4a8): https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577269915\n"
        "• Closed Blocked Pull Request (#1): https://github.com/saikeerthan006-commits/smart-campus-facility-devops/pull/1\n"
        "• Acknowledgement: Problem scenario, baseline 14-test model structure, and report section layout adapted from the SIMATS Engineering CSA10 Software Engineering Assignment 4 specification and reference template; extended with a full FastAPI application, HMAC Bearer RBAC security suite, multi-stage Docker + GitHub Actions pipeline, 5-stage async bounded load harness, point-in-time backup/rollback rehearsal, and Day-4 expand-and-contract migration and durable outbox implementation.",
    )

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT_DOCX))
    print(f"[REPORT GENERATED] {OUT_DOCX} ({OUT_DOCX.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build_report()
