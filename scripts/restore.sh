#!/usr/bin/env bash
# ==============================================================================
# Phoenix - Disaster Recovery as Code
# scripts/restore.sh: Automated SQLite Database Restore Script
# Restores a chosen backup, verifies integrity via PRAGMA integrity_check,
# validates row counts, and logs the recovery event.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BACKUP_FILE="${1:-}"
TARGET_DB="${2:-"${DB_PATH:-"${REPO_ROOT}/backend/phoenix.db"}"}"
BACKUP_DIR="${BACKUP_DIR:-"${REPO_ROOT}/backups"}"

echo "=================================================="
echo " Phoenix Disaster Recovery - Database Restore"
echo "=================================================="
echo "Target DB:        ${TARGET_DB}"
echo "Backup Search:    ${BACKUP_DIR}"

if [ -n "${BACKUP_FILE}" ]; then
    python3 "${SCRIPT_DIR}/restore.py" --backup-file "${BACKUP_FILE}" --target-db "${TARGET_DB}"
else
    python3 "${SCRIPT_DIR}/restore.py" --backup-dir "${BACKUP_DIR}" --target-db "${TARGET_DB}"
fi

echo "=================================================="
echo " Restore completed and verified."
echo "=================================================="
