#!/usr/bin/env python3
"""
Nagios Core Custom Plugin: check_web_errors.py
Parses web server (Nginx/Apache) access logs, counts recent HTTP 5xx server errors,
and triggers Nagios alerts based on configured threshold windows.

Usage:
  python3 check_web_errors.py -l /var/log/nginx/access.log -w 5 -c 20 -m 5
  python3 check_web_errors.py --help

Options:
  -l, --log-file PATH      Path to web access log file (default: /var/log/nginx/access.log)
  -w, --warning INT        Warning threshold for HTTP 5xx count (default: 5)
  -c, --critical INT       Critical threshold for HTTP 5xx count (default: 20)
  -m, --minutes INT        Sliding time window in minutes to inspect (default: 5)

Exit Codes:
  0 = OK (5xx count < warning threshold)
  1 = WARNING (5xx count >= warning threshold)
  2 = CRITICAL (5xx count >= critical threshold)
  3 = UNKNOWN (log file not found or unreadable)
"""
import os
import sys
import argparse
import re
from datetime import datetime, timezone, timedelta

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# Regex matching standard Combined Log Format with status code
LOG_PATTERN = re.compile(
    r'.*\[(?P<timestamp>[\w:/]+\s[+\-]\d{4})\].*"\s(?P<status>5\d{2})\s\d+.*'
)

def parse_log_timestamp(ts_str: str) -> datetime:
    """Parse Nginx access log timestamp e.g. 16/Nov/2026:11:30:00 +0000."""
    try:
        return datetime.strptime(ts_str, "%d/%b/%Y:%H:%M:%S %z")
    except Exception:
        # Fallback without timezone
        clean_ts = ts_str.split()[0]
        return datetime.strptime(clean_ts, "%d/%b/%Y:%H:%M:%S").replace(tzinfo=timezone.utc)

def count_recent_5xx_errors(log_file: str, minutes: int) -> int:
    """Scan log file and count 5xx entries within the last N minutes."""
    if not os.path.exists(log_file):
        print(f"WEB ERRORS UNKNOWN - Log file '{log_file}' does not exist.")
        sys.exit(STATE_UNKNOWN)

    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    count_5xx = 0

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                match = LOG_PATTERN.match(line)
                if match:
                    try:
                        entry_time = parse_log_timestamp(match.group("timestamp"))
                        if entry_time >= cutoff_time:
                            count_5xx += 1
                    except Exception:
                        # If timestamp unparseable, count if 5xx found in window
                        count_5xx += 1
    except PermissionError:
        print(f"WEB ERRORS UNKNOWN - Permission denied reading log file '{log_file}'.")
        sys.exit(STATE_UNKNOWN)
    except Exception as e:
        print(f"WEB ERRORS UNKNOWN - Error parsing log file: {e}")
        sys.exit(STATE_UNKNOWN)

    return count_5xx

def main():
    parser = argparse.ArgumentParser(description="Nagios check_web_errors plugin")
    parser.add_argument("-f", "--file", default="/var/log/nginx/access.log", help="Path to Nginx access log")
    parser.add_argument("-w", "--warning", type=int, default=5, help="Warning threshold for 5xx errors (default: 5)")
    parser.add_argument("-c", "--critical", type=int, default=20, help="Critical threshold for 5xx errors (default: 20)")
    parser.add_argument("-m", "--minutes", type=int, default=5, help="Time window in minutes to evaluate (default: 5)")
    args = parser.parse_args()

    count_5xx = count_recent_5xx_errors(args.file, args.minutes)
    perfdata = f"'errors_5xx'={count_5xx};{args.warning};{args.critical};0;"

    if count_5xx >= args.critical:
        print(f"WEB ERRORS CRITICAL - Found {count_5xx} HTTP 5xx errors in last {args.minutes}m (threshold >= {args.critical}) | {perfdata}")
        sys.exit(STATE_CRITICAL)
    elif count_5xx >= args.warning:
        print(f"WEB ERRORS WARNING - Found {count_5xx} HTTP 5xx errors in last {args.minutes}m (threshold >= {args.warning}) | {perfdata}")
        sys.exit(STATE_WARNING)
    else:
        print(f"WEB ERRORS OK - Found {count_5xx} HTTP 5xx errors in last {args.minutes}m (thresholds: w={args.warning}, c={args.critical}) | {perfdata}")
        sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
