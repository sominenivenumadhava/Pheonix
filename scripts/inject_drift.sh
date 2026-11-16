#!/usr/bin/env bash
# ==============================================================================
# Phoenix - Configuration Drift Injection Script (inject_drift.sh)
# Deliberately tampers with baseline files, permissions, and stops services
# to demonstrate Puppet's automated drift detection and self-healing.
# ==============================================================================
set -euo pipefail

echo "=================================================="
echo " Phoenix - Simulating Intentional System Drift"
echo "=================================================="

# 1. Tamper with managed baseline policy file content
echo "[1/4] Tampering with /etc/phoenix-baseline.conf content..."
if [ -f "/etc/phoenix-baseline.conf" ]; then
    echo "MALICIOUS_UNAUTHORIZED_OVERWRITE=TRUE" | sudo tee -a /etc/phoenix-baseline.conf > /dev/null
    echo "      Appended unauthorized line to /etc/phoenix-baseline.conf"
else
    echo "      Creating rogue /etc/phoenix-baseline.conf with unauthorized state..."
    echo "DRIFT_STATUS=CORRUPTED" | sudo tee /etc/phoenix-baseline.conf > /dev/null
fi

# 2. Loosen file permissions to insecure mode
echo "[2/4] Loosening file permissions to 0777 (Insecure)..."
sudo chmod 0777 /etc/phoenix-baseline.conf
ls -l /etc/phoenix-baseline.conf

# 3. Deliberately stop the managed Nginx service
echo "[3/4] Stopping Nginx web service..."
sudo systemctl stop nginx || true
echo "      Nginx service is now STOPPED (Simulated outage)"

# 4. Show current drifted state
echo "[4/4] Current Drift Status Summary:"
echo "      - Service Nginx status: $(systemctl is-active nginx || echo 'inactive/failed')"
echo "      - Permissions on /etc/phoenix-baseline.conf: $(stat -c '%a' /etc/phoenix-baseline.conf 2>/dev/null || stat -f '%Lp' /etc/phoenix-baseline.conf)"
echo ""
echo "=================================================="
echo " Drift successfully injected!"
echo " Next step: Run 'sudo puppet agent -t' to trigger automated self-healing."
echo "=================================================="
