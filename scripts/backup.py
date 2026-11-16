#!/usr/bin/env python3
"""
Phoenix Automated Database Backup Script
Performs a safe SQLite online snapshot to an external directory,
calculates SHA-256 checksum, verifies database integrity, and records
the event in the backup_records audit table.
"""
import os
import sys
import sqlite3
import hashlib
import argparse
from datetime import datetime, timezone

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 digest of a given file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def verify_backup_integrity(backup_path: str) -> tuple[bool, str]:
    """Execute PRAGMA integrity_check on the snapshot."""
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        conn.close()
        if res and res[0] == "ok":
            return True, "ok"
        return False, str(res)
    except Exception as e:
        return False, str(e)

def perform_backup(db_path: str, backup_dir: str) -> str:
    # Resolve absolute paths
    db_path = os.path.abspath(db_path)
    backup_dir = os.path.abspath(backup_dir)

    if not os.path.exists(db_path):
        print(f"[!] Error: Source database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(backup_dir, exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"phoenix_backup_{timestamp_str}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    print(f"[*] Starting backup from: {db_path}")
    print(f"[*] Destination: {backup_path}")

    # Use SQLite Online Backup API for lock-safe atomic snapshot
    source_conn = sqlite3.connect(db_path)
    dest_conn = sqlite3.connect(backup_path)
    try:
        source_conn.backup(dest_conn)
        dest_conn.close()
        print(f"[+] Snapshot created successfully.")
    except Exception as e:
        print(f"[!] Backup snapshot failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Calculate file size and checksum
    file_size = os.path.getsize(backup_path)
    checksum = compute_sha256(backup_path)
    print(f"[+] File Size: {file_size} bytes")
    print(f"[+] SHA-256: {checksum}")

    # Verify integrity of the snapshot
    ok, integrity_msg = verify_backup_integrity(backup_path)
    if not ok:
        print(f"[!] Warning: Integrity check failed on backup: {integrity_msg}", file=sys.stderr)
    else:
        print(f"[+] Integrity check: PASSED (PRAGMA integrity_check = ok)")

    # Log record in source database backup_records table
    try:
        cursor = source_conn.cursor()
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO backup_records (timestamp, location, size_bytes, checksum_sha256, restore_verified, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now_utc, backup_path, file_size, checksum, False, f"Integrity: {integrity_msg}", now_utc))
        source_conn.commit()
        print(f"[+] Logged entry into backup_records table.")
    except Exception as e:
        print(f"[*] Note: Could not log to backup_records table ({e}).", file=sys.stderr)
    finally:
        source_conn.close()

    return backup_path

def main():
    parser = argparse.ArgumentParser(description="Phoenix Database Backup Utility")
    default_backup = os.getenv("BACKUP_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backups")))
    default_db = os.getenv("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "phoenix.db")))
    parser.add_argument("--db-path", default=default_db,
                        help="Path to source SQLite database")
    parser.add_argument("--backup-dir", default=default_backup,
                        help="External directory for storing backups")
    args = parser.parse_args()

    perform_backup(args.db_path, args.backup_dir)

if __name__ == "__main__":
    main()
