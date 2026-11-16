#!/usr/bin/env bash
# ==============================================================================
# Phoenix - Simulate Application Failure Script
# Deliberately stops the phoenix-backend service and logs a SERVICE_FAILURE event
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/simulate_failure.py"
