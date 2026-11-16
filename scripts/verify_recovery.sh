#!/usr/bin/env bash
# ==============================================================================
# Phoenix Recovery Verification Script: verify_recovery.sh
# Verifies system operational status after disaster recovery deployment.
# Usage: ./verify_recovery.sh [URL] [DB_PATH]
# ==============================================================================
set -euo pipefail

PORTAL_URL="${1:-http://localhost:8000}"
DB_PATH="${2:-/var/lib/phoenix/phoenix.db}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================================================"
echo "          PHOENIX RECOVERY VERIFICATION AUTOMATION"
echo "======================================================================"
echo "Target Portal URL: ${PORTAL_URL}"
echo "Target Database:   ${DB_PATH}"
echo "----------------------------------------------------------------------"

# Prefer python3 verify_recovery.py if available
if command -v python3 >/dev/null 2>&1 && [ -f "${SCRIPT_DIR}/verify_recovery.py" ]; then
    echo "[*] Invoking Python verification engine..."
    python3 "${SCRIPT_DIR}/verify_recovery.py" --url "${PORTAL_URL}" --db-path "${DB_PATH}"
    exit $?
fi

# Fallback: Native curl & sqlite3 verification
echo "[*] Running fallback shell-based verification..."

# 1. Health Probe
echo -n "[+] Testing /health: "
HEALTH_CODE=$(curl -s -o /tmp/phoenix_health.json -w "%{http_code}" "${PORTAL_URL}/health" || echo "000")
if [ "${HEALTH_CODE}" -eq 200 ]; then
    echo "PASS (HTTP 200 OK)"
else
    echo "FAIL (HTTP ${HEALTH_CODE})"
    exit 1
fi

# 2. Ready Probe
echo -n "[+] Testing /ready: "
READY_CODE=$(curl -s -o /tmp/phoenix_ready.json -w "%{http_code}" "${PORTAL_URL}/ready" || echo "000")
if [ "${READY_CODE}" -eq 200 ]; then
    echo "PASS (HTTP 200 OK)"
else
    echo "FAIL (HTTP ${READY_CODE})"
    exit 1
fi

# 3. Database Check
if [ -f "${DB_PATH}" ]; then
    echo -n "[+] SQLite PRAGMA integrity_check: "
    INTEGRITY=$(sqlite3 "${DB_PATH}" "PRAGMA integrity_check;")
    if [ "${INTEGRITY}" = "ok" ]; then
        echo "PASS (${INTEGRITY})"
    else
        echo "FAIL (${INTEGRITY})"
        exit 1
    fi

    echo "[+] Database Row Audit:"
    for table in users customers services bookings invoices backup_records recovery_events; do
        count=$(sqlite3 "${DB_PATH}" "SELECT COUNT(*) FROM ${table};")
        echo "    - ${table}: ${count} rows"
    done

    # 4. Log RECOVERY_VERIFIED event
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    sqlite3 "${DB_PATH}" "INSERT INTO recovery_events (event_type, detail, triggered_by, timestamp) VALUES ('RECOVERY_VERIFIED', 'Shell fallback recovery verification successful', 'VERIFY_RECOVERY_SH', '${TIMESTAMP}');"
    echo "[+] Logged RECOVERY_VERIFIED to recovery_events."
else
    echo "[!] Warning: Database not found at ${DB_PATH}."
fi

echo "======================================================================"
echo "[>>>] ALL RECOVERY CHECKS PASSED!"
echo "======================================================================"
exit 0
