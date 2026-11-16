#!/usr/bin/env python3
"""
Nagios Core Custom Plugin: check_portal_health.py
Probes the Phoenix application /health endpoint, checks database connectivity,
measures response latency, and outputs Nagios-compliant status with performance data.

Exit Codes:
  0 = OK
  1 = WARNING (latency exceeds warning threshold)
  2 = CRITICAL (service down, DB failed, HTTP 5xx, or latency exceeds critical)
  3 = UNKNOWN (invalid arguments, network timeout, or unexpected exception)
"""
import sys
import time
import argparse
import urllib.request
import urllib.error
import json

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

def check_portal_health(host: str, port: int, path: str, warning_ms: float, critical_ms: float, timeout_s: float):
    # Construct endpoint URL
    if not path.startswith('/'):
        path = '/' + path
    url = f"http://{host}:{port}{path}"

    start_time = time.perf_counter()
    try:
        # Build direct opener bypassing any environment proxy settings
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(url, headers={"User-Agent": "Nagios-check_portal_health/1.0"})
        with opener.open(req, timeout=timeout_s) as response:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            status_code = response.getcode()
            body_bytes = response.read()

        # Parse JSON payload
        try:
            data = json.loads(body_bytes.decode('utf-8'))
        except Exception as e:
            print(f"PORTAL HEALTH WARNING - HTTP {status_code} received but invalid JSON payload: {e} | 'time'={elapsed_ms:.1f}ms;{warning_ms};{critical_ms};0;")
            sys.exit(STATE_WARNING)

        portal_status = data.get("status", "unknown")
        db_status = data.get("db", "unknown")
        app_version = data.get("version", "1.0.0")

        perfdata = f"'time'={elapsed_ms:.1f}ms;{warning_ms:.1f};{critical_ms:.1f};0;"

        # Check for service/database failures
        if status_code != 200 or portal_status.lower() != "healthy" or db_status.lower() != "ok":
            print(f"PORTAL HEALTH CRITICAL - HTTP {status_code}, status={portal_status}, db={db_status} | {perfdata}")
            sys.exit(STATE_CRITICAL)

        # Check performance thresholds
        if elapsed_ms >= critical_ms:
            print(f"PORTAL HEALTH CRITICAL - Response time {elapsed_ms:.1f}ms exceeds critical threshold {critical_ms}ms (db={db_status}, v={app_version}) | {perfdata}")
            sys.exit(STATE_CRITICAL)
        elif elapsed_ms >= warning_ms:
            print(f"PORTAL HEALTH WARNING - Response time {elapsed_ms:.1f}ms exceeds warning threshold {warning_ms}ms (db={db_status}, v={app_version}) | {perfdata}")
            sys.exit(STATE_WARNING)
        else:
            print(f"PORTAL HEALTH OK - HTTP {status_code}, status={portal_status}, db={db_status} ({elapsed_ms:.1f}ms, v={app_version}) | {perfdata}")
            sys.exit(STATE_OK)

    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        perfdata = f"'time'={elapsed_ms:.1f}ms;{warning_ms:.1f};{critical_ms:.1f};0;"
        print(f"PORTAL HEALTH CRITICAL - HTTP {e.code} ({e.reason}) | {perfdata}")
        sys.exit(STATE_CRITICAL)

    except urllib.error.URLError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        perfdata = f"'time'={elapsed_ms:.1f}ms;{warning_ms:.1f};{critical_ms:.1f};0;"
        print(f"PORTAL HEALTH CRITICAL - Connection refused or host unreachable: {e.reason} | {perfdata}")
        sys.exit(STATE_CRITICAL)

    except TimeoutError:
        print(f"PORTAL HEALTH CRITICAL - Connection timed out after {timeout_s}s | 'time'={timeout_s * 1000.0:.1f}ms;{warning_ms:.1f};{critical_ms:.1f};0;")
        sys.exit(STATE_CRITICAL)

    except Exception as e:
        print(f"PORTAL HEALTH UNKNOWN - Unexpected error checking health: {e}")
        sys.exit(STATE_UNKNOWN)

def main():
    parser = argparse.ArgumentParser(description="Nagios check_portal_health plugin")
    parser.add_argument("-H", "--host", default="127.0.0.1", help="Target hostname or IP address")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target HTTP port (default: 80)")
    parser.add_argument("-u", "--url", default="/health", help="Health probe endpoint URI (default: /health)")
    parser.add_argument("-w", "--warning", type=float, default=500.0, help="Warning latency threshold in milliseconds (default: 500)")
    parser.add_argument("-c", "--critical", type=float, default=1500.0, help="Critical latency threshold in milliseconds (default: 1500)")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Socket timeout in seconds (default: 5.0)")
    args = parser.parse_args()

    check_portal_health(
        host=args.host,
        port=args.port,
        path=args.url,
        warning_ms=args.warning,
        critical_ms=args.critical,
        timeout_s=args.timeout
    )

if __name__ == "__main__":
    main()
