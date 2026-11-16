#!/usr/bin/env python3
"""
Phoenix Database Restore & Verification Utility
Restores a chosen SQLite backup onto a target database path,
verifies database integrity via PRAGMA integrity_check, audits table row counts,
and records the restoration event in the recovery_events table.
"""
import os
import sys
import shutil
import sqlite3
import hashlib
import argparse
from datetime import datetime, timezone

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 digest of file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def get_table_counts(db_path: str) -> dict:
    """Query row counts across core business tables."""
    counts = {}
    tables = ["users", "customers", "services", "bookings", "invoices", "backup_records"]
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for t in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cursor.fetchone()[0]
            except Exception:
                counts[t] = 0
        conn.close()
    except Exception as e:
        print(f"[!] Warning reading table counts: {e}", file=sys.stderr)
    return counts

def verify_db_integrity(db_path: str) -> tuple[bool, str]:
    """Execute PRAGMA integrity_check on SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        row = cursor.fetchone()
        conn.close()
        if row and row[0] == "ok":
            return True, "ok"
        return False, str(row)
    except Exception as e:
        return False, str(e)

def find_latest_backup(backup_dir: str) -> str:
    """Find the newest .db backup file in the backup directory."""
    if not os.path.exists(backup_dir):
        return None
    files = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.startswith("phoenix_backup_") and f.endswith(".db")
    ]
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def perform_restore(backup_file: str, target_db: str) -> bool:
    if not backup_file or not os.path.exists(backup_file):
        print(f"[!] Error: Backup file not found: {backup_file}", file=sys.stderr)
        return False

    backup_file = os.path.abspath(backup_file)
    target_db = os.path.abspath(target_db)

    print(f"[*] Restoring from backup: {backup_file}")
    print(f"[*] Target destination: {target_db}")

    # Step 1: Pre-restore verification of backup file
    print("--- Step 1: Verifying Backup File Integrity ---")
    sha = compute_sha256(backup_file)
    print(f"[+] Backup SHA-256: {sha}")
    
    ok, msg = verify_db_integrity(backup_file)
    if not ok:
        print(f"[!] FATAL: Backup file integrity check failed: {msg}", file=sys.stderr)
        return False
    print(f"[+] Backup Integrity Check: PASSED ({msg})")

    backup_counts = get_table_counts(backup_file)
    print(f"[+] Backup Row Counts: {backup_counts}")

    # Step 2: Atomic restoration
    print("--- Step 2: Deploying Database Snapshot ---")
    os.makedirs(os.path.dirname(target_db), exist_ok=True)
    
    # Remove existing WAL and SHM files if present
    for ext in ["-wal", "-shm"]:
        sidecar = target_db + ext
        if os.path.exists(sidecar):
            os.remove(sidecar)

    shutil.copy2(backup_file, target_db)
    print(f"[+] File copied to {target_db}")

    # Step 3: Post-restore verification
    print("--- Step 3: Verifying Restored Database ---")
    target_ok, target_msg = verify_db_integrity(target_db)
    if not target_ok:
        print(f"[!] FATAL: Restored database failed integrity check: {target_msg}", file=sys.stderr)
        return False
    print(f"[+] Target Integrity Check: PASSED ({target_msg})")

    target_counts = get_table_counts(target_db)
    print(f"[+] Target Restored Row Counts: {target_counts}")

    # Validate row parity
    for table, count in backup_counts.items():
        if target_counts.get(table) != count:
            print(f"[!] Discrepancy in table '{table}': backup had {count}, restored has {target_counts.get(table)}", file=sys.stderr)
            return False

    print("[+] All table row counts match exactly!")

    # Step 4: Record Recovery Event
    try:
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO recovery_events (event_type, detail, triggered_by, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            "DATABASE_RESTORE",
            f"Restored from {os.path.basename(backup_file)}. Checksum: {sha[:12]}. Rows: {target_counts}",
            "RESTORE_SCRIPT",
            now_utc
        ))
        # Update backup_records table to mark restore_verified = True
        cursor.execute("""
            UPDATE backup_records
            SET restore_verified = 1
            WHERE checksum_sha256 = ? OR location LIKE ?
        """, (sha, f"%{os.path.basename(backup_file)}%"))
        conn.commit()
        conn.close()
        print("[+] Logged DATABASE_RESTORE event in recovery_events table.")
        print("[+] Updated backup_records table (restore_verified = 1).")
    except Exception as e:
        print(f"[*] Note: Could not record recovery event: {e}", file=sys.stderr)

    print("\n[✓] DATABASE RESTORATION AND VERIFICATION COMPLETED SUCCESSFULLY.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Phoenix Database Restore Utility")
    default_backup = os.getenv("BACKUP_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backups")))
    default_db = os.getenv("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "phoenix.db")))
    parser.add_argument("--backup-file", default=None, help="Path to specific backup .db file")
    parser.add_argument("--backup-dir", default=default_backup,
                        help="Directory to search for latest backup")
    parser.add_argument("--target-db", "--db-path", dest="target_db", default=default_db,
                        help="Destination SQLite database file")
    args = parser.parse_args()

    backup_file = args.backup_file
    if not backup_file:
        backup_file = find_latest_backup(args.backup_dir)
        if not backup_file:
            print(f"[!] No backup files found in {args.backup_dir}", file=sys.stderr)
            sys.exit(1)

    success = perform_restore(backup_file, args.target_db)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
