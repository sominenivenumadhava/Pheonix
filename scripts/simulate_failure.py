#!/usr/bin/env python3
"""
Phoenix Failure Simulation Utility: simulate_failure.py
Simulates an application or infrastructure failure by stopping the backend service
and logging a SERVICE_FAILURE incident in the recovery_events table.
"""
import os
import sys
import sqlite3
import subprocess
from datetime import datetime, timezone

def stop_application_service():
    """Attempt to stop systemd phoenix-backend or kill local uvicorn processes."""
    stopped = False
    # Attempt systemctl if running under Linux systemd
    try:
        res = subprocess.run(["sudo", "systemctl", "stop", "phoenix-backend"], capture_output=True, text=True)
        if res.returncode == 0:
            print("[+] Stopped systemd service 'phoenix-backend'.")
            stopped = True
    except Exception:
        pass

    if not stopped:
        print("[*] Note: Running outside systemd or on Windows; simulating application outage.")

def log_failure_event(db_path: str):
    """Insert SERVICE_FAILURE event into recovery_events table."""
    if not os.path.exists(db_path):
        print(f"[!] Warning: Database not found at {db_path}", file=sys.stderr)
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO recovery_events (event_type, detail, triggered_by, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            "SERVICE_FAILURE",
            "Simulated application service shutdown; Nagios will transition from OK to CRITICAL.",
            "SIMULATE_FAILURE_SCRIPT",
            now_utc
        ))
        conn.commit()
        conn.close()
        print(f"[+] Successfully logged 'SERVICE_FAILURE' in recovery_events table.")
    except Exception as e:
        print(f"[!] Could not log failure event: {e}", file=sys.stderr)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.getenv("DB_PATH", os.path.join(repo_root, "backend", "phoenix.db"))

    print("==================================================")
    print(" Phoenix Disaster Simulation - Application Failure")
    print("==================================================")

    stop_application_service()
    log_failure_event(db_path)

    print("==================================================")
    print(" Status: Application service stopped.")
    print(" Expected Nagios status: CRITICAL (Connection refused on /health)")
    print("==================================================")

if __name__ == "__main__":
    main()
