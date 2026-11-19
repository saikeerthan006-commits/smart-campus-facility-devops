#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
echo "=================================================================="
echo "[SMOKE-GATE] Starting Post-Deployment Smoke Verification against ${BASE_URL}"
echo "=================================================================="

python3 scripts/smoke_test.py --base-url "${BASE_URL}"
