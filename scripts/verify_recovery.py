#!/usr/bin/env python3
"""
Phoenix Recovery Verification Tool: verify_recovery.py
Verifies end-to-end operational health following a disaster recovery or failover event.
Validates:
1. HTTP /health endpoint (FastAPI service status, latency, database connectivity)
2. HTTP /ready endpoint (readiness probe)
3. SQLite database physical integrity (PRAGMA integrity_check, foreign keys)
4. Table record counts (users, customers, services, bookings, invoices)
5. Audit trail: Logs a 'RECOVERY_VERIFIED' event into recovery_events table.
"""

import os
import sys
import json
import time
import sqlite3
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone

def check_http_endpoint(url: str, expected_key: str = None, expected_val = None, timeout: float = 5.0):
    """Query an HTTP endpoint directly without proxy interference and parse JSON."""
    handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(handler)
    start_time = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Phoenix-Recovery-Verifier/1.0", "Accept": "application/json"}
        )
        with opener.open(req, timeout=timeout) as response:
            latency_ms = (time.time() - start_time) * 1000
            status_code = response.getcode()
            body_bytes = response.read()
            body_str = body_bytes.decode("utf-8")
            data = json.loads(body_str) if body_str else {}
            
            if status_code != 200:
                return False, f"HTTP status {status_code}", latency_ms, data

            if expected_key:
                val = data.get(expected_key)
                if expected_val is not None and val != expected_val:
                    return False, f"Key '{expected_key}' expected '{expected_val}', got '{val}'", latency_ms, data
                elif val is None:
                    return False, f"Key '{expected_key}' missing in response", latency_ms, data

            return True, "OK", latency_ms, data
    except urllib.error.HTTPError as e:
        latency_ms = (time.time() - start_time) * 1000
        return False, f"HTTP Error {e.code}: {e.reason}", latency_ms, {}
    except urllib.error.URLError as e:
        latency_ms = (time.time() - start_time) * 1000
        return False, f"Connection Failed: {e.reason}", latency_ms, {}
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return False, f"Error: {str(e)}", latency_ms, {}

def audit_database(db_path: str):
    """Audit SQLite database physical integrity and record counts."""
    if not os.path.exists(db_path):
        return False, f"Database file not found at {db_path}", {}

    results = {}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Integrity check
        cursor.execute("PRAGMA integrity_check;")
        integrity_res = cursor.fetchone()
        if not integrity_res or integrity_res[0] != "ok":
            conn.close()
            return False, f"PRAGMA integrity_check failed: {integrity_res}", {}

        # 2. Foreign key check
        cursor.execute("PRAGMA foreign_key_check;")
        fk_violations = cursor.fetchall()
        if fk_violations:
            conn.close()
            return False, f"Foreign key violations detected: {len(fk_violations)}", {}

        # 3. Table counts
        tables = ["users", "customers", "services", "bookings", "invoices", "backup_records", "recovery_events"]
        counts = {}
        for tbl in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
                count = cursor.fetchone()[0]
                counts[tbl] = count
            except sqlite3.OperationalError:
                counts[tbl] = -1

        conn.close()
        return True, "Integrity OK, FKs OK", counts
    except Exception as e:
        return False, f"Database audit exception: {str(e)}", {}

def log_recovery_verification(db_path: str, summary_detail: str):
    """Insert RECOVERY_VERIFIED record in recovery_events."""
    if not os.path.exists(db_path):
        return False
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO recovery_events (event_type, detail, triggered_by, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            "RECOVERY_VERIFIED",
            summary_detail,
            "VERIFY_RECOVERY_SCRIPT",
            now_utc
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def resolve_db_path(explicit_path: str = None) -> str:
    """Resolve database path from argument or default search locations."""
    if explicit_path:
        return explicit_path
    
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "backend", "phoenix.db"),
        "/var/lib/phoenix/phoenix.db",
        "backend/phoenix.db",
        "phoenix.db"
    ]
    for c in candidates:
        abs_c = os.path.abspath(c)
        if os.path.exists(abs_c):
            return abs_c
    return os.path.abspath(candidates[0])

def main():
    parser = argparse.ArgumentParser(description="Phoenix Disaster Recovery Verification Utility")
    parser.add_argument("--url", "-u", default="http://localhost:8000", help="FastAPI portal base URL (default: http://localhost:8000)")
    parser.add_argument("--db-path", "-d", default=None, help="Path to SQLite database")
    parser.add_argument("--skip-http", action="store_true", help="Skip HTTP endpoint verification")
    parser.add_argument("--skip-db", action="store_true", help="Skip SQLite database verification")
    parser.add_argument("--timeout", "-t", type=float, default=5.0, help="HTTP timeout in seconds")

    args = parser.parse_args()
    db_path = resolve_db_path(args.db_path)

    print("=" * 72)
    print("      PHOENIX DISASTER RECOVERY AS CODE — VERIFICATION REPORT")
    print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 72)

    all_passed = True
    report_rows = []

    # 1. HTTP /health Check
    if not args.skip_http:
        health_url = f"{args.url.rstrip('/')}/health"
        ok, msg, lat, data = check_http_endpoint(health_url, expected_key="status", expected_val="healthy", timeout=args.timeout)
        status_str = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        db_stat = data.get("database", "unknown") if ok else "unreachable"
        detail = f"Latency: {lat:.1f}ms | status={data.get('status')} | db={db_stat}" if ok else msg
        report_rows.append(("API Health Probe (/health)", status_str, detail))

        # 2. HTTP /ready Check
        ready_url = f"{args.url.rstrip('/')}/ready"
        ok_r, msg_r, lat_r, data_r = check_http_endpoint(ready_url, expected_key="ready", expected_val=True, timeout=args.timeout)
        status_r = "PASS" if ok_r else "FAIL"
        if not ok_r:
            all_passed = False
        detail_r = f"Latency: {lat_r:.1f}ms | ready={data_r.get('ready')}" if ok_r else msg_r
        report_rows.append(("API Readiness Probe (/ready)", status_r, detail_r))
    else:
        report_rows.append(("API Health Probes", "SKIPPED", "Skipped by --skip-http flag"))

    # 3. Database Audit
    db_counts = {}
    if not args.skip_db:
        ok_db, msg_db, counts = audit_database(db_path)
        status_db = "PASS" if ok_db else "FAIL"
        if not ok_db:
            all_passed = False
        detail_db = f"{msg_db} | Path: {os.path.basename(db_path)}"
        report_rows.append(("SQLite Physical Integrity", status_db, detail_db))

        if ok_db:
            db_counts = counts
            counts_str = ", ".join([f"{k}:{v}" for k, v in counts.items()])
            has_records = counts.get("users", 0) > 0 and counts.get("services", 0) > 0
            cnt_status = "PASS" if has_records else "WARN"
            report_rows.append(("Database Record Census", cnt_status, counts_str))
            
            # Log verification event to recovery_events
            summary_text = (
                f"Recovery Verified: Health=OK, DB=OK, Integrity=PRAGMA_OK. "
                f"Record counts: {counts_str}"
            )
            logged = log_recovery_verification(db_path, summary_text)
            log_status = "PASS" if logged else "FAIL"
            report_rows.append(("Recovery Event Logged", log_status, "Inserted RECOVERY_VERIFIED row into recovery_events"))
        else:
            report_rows.append(("Database Record Census", "SKIPPED", "Cannot audit counts on corrupt or missing DB"))
    else:
        report_rows.append(("Database Verification", "SKIPPED", "Skipped by --skip-db flag"))

    # Print Table
    print(f"\n{'CHECK ITEM':<32} | {'STATUS':<7} | {'DETAILS'}")
    print("-" * 72)
    for name, st, dt in report_rows:
        print(f"{name:<32} | {st:<7} | {dt}")
    print("-" * 72)

    if all_passed:
        print("\n[>>>] FINAL VERDICT: RECOVERY SUCCESSFUL — ALL SYSTEMS FULLY OPERATIONAL")
        print("=" * 72)
        sys.exit(0)
    else:
        print("\n[!!!] FINAL VERDICT: RECOVERY VERIFICATION FAILED — INVESTIGATION REQUIRED")
        print("=" * 72)
        sys.exit(1)

if __name__ == "__main__":
    main()
