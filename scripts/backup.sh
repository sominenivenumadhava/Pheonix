#!/usr/bin/env bash
# ==============================================================================
# Phoenix - Disaster Recovery as Code
# scripts/backup.sh: Automated SQLite Database Backup Script
# Copies SQLite DB to a configurable external directory outside the app folder
# and records the operation in the backup_records table.
# ==============================================================================
set -euo pipefail

# Configurable paths with sensible defaults
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DB_PATH="${DB_PATH:-"${REPO_ROOT}/backend/phoenix.db"}"
BACKUP_DIR="${BACKUP_DIR:-"${REPO_ROOT}/backups"}"

echo "=================================================="
echo " Phoenix Disaster Recovery - Database Backup"
echo "=================================================="
echo "Source Database:   ${DB_PATH}"
echo "Backup Directory:  ${BACKUP_DIR}"

# Run the cross-platform Python backup engine
python3 "${SCRIPT_DIR}/backup.py" --db-path "${DB_PATH}" --backup-dir "${BACKUP_DIR}"

echo "=================================================="
echo " Backup completed successfully."
echo "=================================================="
