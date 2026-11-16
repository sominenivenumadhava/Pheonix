#!/usr/bin/env bash
# ==============================================================================
# Nagios Custom Plugin: check_web_errors.sh
# Counts recent HTTP 5xx errors from the Nginx access log
# Exit codes: 0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN
# ==============================================================================
set -euo pipefail

STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3

LOG_FILE="/var/log/nginx/access.log"
WARN_THRESH=5
CRIT_THRESH=20
WINDOW_MIN=5

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--file)
            LOG_FILE="$2"
            shift 2
            ;;
        -w|--warning)
            WARN_THRESH="$2"
            shift 2
            ;;
        -c|--critical)
            CRIT_THRESH="$2"
            shift 2
            ;;
        -m|--minutes)
            WINDOW_MIN="$2"
            shift 2
            ;;
        *)
            echo "WEB ERRORS UNKNOWN - Unknown option: $1"
            exit $STATE_UNKNOWN
            ;;
    esac
done

if [ ! -f "$LOG_FILE" ]; then
    echo "WEB ERRORS UNKNOWN - Log file '$LOG_FILE' does not exist."
    exit $STATE_UNKNOWN
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1 && [ -f "${SCRIPT_DIR}/check_web_errors.py" ]; then
    exec python3 "${SCRIPT_DIR}/check_web_errors.py" -f "$LOG_FILE" -w "$WARN_THRESH" -c "$CRIT_THRESH" -m "$WINDOW_MIN"
fi

# Fallback pure shell log parsing
ERRORS_5XX=$(grep -E ' HTTP/[0-9.]+" 5[0-9]{2} ' "$LOG_FILE" 2>/dev/null | tail -n 1000 | wc -l || echo "0")
PERFDATA="'errors_5xx'=${ERRORS_5XX};${WARN_THRESH};${CRIT_THRESH};0;"

if [ "$ERRORS_5XX" -ge "$CRIT_THRESH" ]; then
    echo "WEB ERRORS CRITICAL - Found $ERRORS_5XX HTTP 5xx errors (critical >= $CRIT_THRESH) | $PERFDATA"
    exit $STATE_CRITICAL
elif [ "$ERRORS_5XX" -ge "$WARN_THRESH" ]; then
    echo "WEB ERRORS WARNING - Found $ERRORS_5XX HTTP 5xx errors (warning >= $WARN_THRESH) | $PERFDATA"
    exit $STATE_WARNING
else
    echo "WEB ERRORS OK - Found $ERRORS_5XX HTTP 5xx errors (thresholds: w=$WARN_THRESH, c=$CRIT_THRESH) | $PERFDATA"
    exit $STATE_OK
fi
