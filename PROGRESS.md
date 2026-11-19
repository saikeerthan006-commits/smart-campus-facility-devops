# CSA10 Software Engineering — Assignment 4 Progress & Evidence Ledger

## Student & Repository Metadata
- **Student Name:** Keerthan M
- **Register Number:** 1925260006
- **Programme and Section:** AIML (B.E. / B.Tech. Artificial Intelligence and Machine Learning)
- **Submission Date:** 18/11/2026
- **GitHub Username:** `saikeerthan006-commits`
- **GitHub Repository URL:** `https://github.com/saikeerthan006-commits/smart-campus-facility-devops`

## Live GitHub Actions Pipeline Runs & Container Identifiers
- **Passing Release Commit SHA (`main`):** `201117de779cf011da5dcb4353979d3c8de0b7d7` (short: `201117d`)
- **Passing GitHub Actions Run ID & URL:** Run `#44577255849` — `https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577255849`
  - **Stage 1 (`test-and-security`):** Succeeded in `37s` (Job ID `135747971370`; Ruff lint 0 errors, secret scan 0 credentials, Day-4 migration gate `MIGRATION_SUCCESS`, Bandit SAST 0 issues, Pytest `30 passed in 1.78s`, `82%` coverage)
  - **Stage 2 (`build-deploy-smoke`):** Succeeded in `1m 12s` (Job ID `135748383966`; Multi-stage Docker build, Trivy scan, Docker Compose isolated stack, `./scripts/smoke-test.sh` passed, `scripts/recovery_rehearsal.py` passed)
  - **Docker Image Tag:** `campus-backend:201117de779cf011da5dcb4353979d3c8de0b7d7`
  - **Docker Image SHA256 Digest:** `sha256:e4d522ba641e7c06d004e4122ce7e690f107fec3ef07a378ac0942b853890611`
- **Blocked Defective Release Branch & Commit SHA:** `demo/defect-threshold-gate` — `2f3e4a8bfd64362515f14906d74e99c209439051` (short: `2f3e4a8`)
- **Blocked GitHub Actions Run ID & URL:** Run `#44577269915` — `https://github.com/saikeerthan006-commits/smart-campus-facility-devops/actions/runs/44577269915`
  - **Stage 1 (`test-and-security`):** Failed in `33s` (`FAILED tests/test_model.py::test_U6_temperature_threshold`, `2 failed, 28 passed`, uploaded failure artifact `test-and-security-reports-2f3e4a8bfd64362515f14906d74e99c209439051`)
  - **Stage 2 (`build-deploy-smoke`):** Automatically `Skipped` / blocked by quality gate
- **Blocked Pull Request URL:** `https://github.com/saikeerthan006-commits/smart-campus-facility-devops/pull/1` (Closed without merging)

## Executed Test, Load, Migration & Recovery Metrics
- **Automated Test Suite:** `30 passed in 2.70s` locally (`1.78s` on GitHub Actions Ubuntu), `82%` overall statement coverage (`472` stmts, `84` missed; `campus_model.py`: `89%`, `app/integrations.py`: `95%`, `app/auth.py`: `84%`).
- **Controlled Defect 1 (`>` -> `>=` in `breached`):** Caught by `test_U6_temperature_threshold` (`assert (True, True) == (False, True)`).
- **Controlled Defect 2 (`('High','High'): 'M1'` -> `'M2'`):** Caught by `test_U1_high_high_is_M1` and `test_U10_priority_matrix_all_nine_cells` (`AssertionError: assert 'M2' == 'M1'`).
- **Bounded Load Experiment (`loadtest/run_bounded_load.py`):**
  - Stage 1 (10 clients, 120 reqs): `193.84 req/s`, `p50 = 47.79 ms`, `p95 = 91.07 ms`, `p99 = 132.30 ms`, `0` 5xx errors
  - Stage 2 (25 clients, 250 reqs): `174.33 req/s`, `p50 = 127.87 ms`, `p95 = 288.78 ms`, `p99 = 337.97 ms`, `0` 5xx errors
  - Stage 3 (50 clients, 400 reqs): `116.21 req/s`, `p50 = 360.47 ms`, `p95 = 825.99 ms`, `p99 = 993.35 ms`, `0` 5xx errors
  - Stage 4 (50-event Sensor Replay Burst: 25 duplicate + 25 unique): `100.38 req/s`, `p50 = 363.06 ms`, `p95 = 470.82 ms`, `26/26` exact tickets created
  - Stage 5 (Dependency Outage `EXTERNAL_SYNC_FAIL=true`, 15 clients, 90 reqs): `116.81 req/s`, `p50 = 111.71 ms`, `p95 = 212.44 ms`, `0` 5xx errors, `46` Pending outbox intents preserved
- **Rehearsed Failure & Rollback Recovery (`scripts/recovery_rehearsal.py`):**
  - Pre-release SQL dump `pre_release_v1.sql` (`3,510` bytes, `sha256:acf3c67c16e24142b3139548...`) and snapshot `pre_release_v1.db` (`36,864` bytes, `sha256:192c7d514bf56323c5916494...`)
  - Faulty release `v2.0.0-broken` detected automatically via `/ready` HTTP `503`
  - Measured rollback & database snapshot restoration duration (RTO): `0.0095 seconds` with `100%` row retention (`{'bookings': 2, 'tickets': 1, 'audit': 3, 'policies': 2, 'integration_outbox': 3}`)
- **Day-4 Expand-and-Contract Migration (`migrations/002_campus_policies_and_outbox.py`):**
  - Controlled failure rehearsal: `MIGRATION_ABORTED_AND_RESTORED` (`{'bookings': 3, 'tickets': 2, 'audit': 5}` restored cleanly)
  - Full migration execution: `MIGRATION_SUCCESS` (`{'bookings': 3, 'tickets': 2, 'audit': 5, 'policies': 2}`)

## Verified Real Screenshots (`evidence/screenshots/`)
1. `01_pytest_baseline_pass.png` (1024x658, 246.1 KB)
2. `02_defect1_threshold_fail.png` (1024x658, 181.4 KB)
3. `03_defect2_priority_fail.png` (1024x658, 183.1 KB)
4. `04_live_app_ui.png` (1024x658, 172.1 KB)
5. `05_docker_smoke_pass.png` (1024x695, 89.4 KB)
6. `06_github_secrets.png` (1024x993, 199.9 KB)
7. `07_gha_success_overview.png` (1024x993, 160.2 KB)
8. `08_gha_success_logs.png` (1024x993, 242.8 KB)
9. `09_gha_blocked_overview.png` (1024x993, 140.6 KB)
10. `10_gha_blocked_log.png` (1024x993, 174.2 KB)
11. `11_github_pr_blocked.png` (1024x993, 201.5 KB)
12. `12_security_rbac_test.png` (1024x695, 79.9 KB)
13. `13_bounded_load_results.png` (1024x658, 160.3 KB)
14. `14_recovery_rollback.png` (1024x695, 185.1 KB)
15. `15_day4_migration_and_tests.png` (1024x695, 141.2 KB)
16. `16_day4_gha_pipeline_pass.png` (652x1024, 196.1 KB)

## Phase Completion Checklist
- [x] **Phase 0: Pre-Flight Check & GitHub Setup**
- [x] **Phase 1: Build Representative Smart Campus Facility Platform**
- [x] **Phase 2: Layered Automated Tests & Controlled Defects (Q2 & Q3)**
- [x] **Phase 3: DevOps Pipeline, GitHub Actions & Browser Evidence (Q4)**
- [x] **Phase 4: Reliability, Security, Bounded Load & Recovery Rehearsal (Q5)**
- [x] **Phase 5: Day-4 Changed Release Adaptation (Q6)**
- [x] **Phase 6: Real Screenshot Audit (16/16 verified PNGs)**
- [x] **Phase 7: Generate Final Word Document (`report/CSA10_Assignment4_Smart_Campus_Report.docx`)**
- [x] **Phase 8: Final Handoff & Verification Summary**
