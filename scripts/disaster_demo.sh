#!/usr/bin/env bash
# ==============================================================================
# Phoenix Disaster Recovery Demonstration Script: disaster_demo.sh
# Automates the end-to-end 8-stage disaster recovery lifecycle drill.
# Usage: ./scripts/disaster_demo.sh [aws|virtualbox]
# ==============================================================================
set -euo pipefail

TARGET_ENV="${1:-virtualbox}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================================================"
echo "      PROJECT PHOENIX: DISASTER RECOVERY DRILL ORCHESTRATOR"
echo "  Target Infrastructure: ${TARGET_ENV^^}"
echo "  Timestamp: $(date -u +"%Y-%m-%d %H:%M:%SZ")"
echo "========================================================================"

# STAGE 1: Live Snapshot Backup
echo ""
echo "=== STAGE 1: Creating Live Pre-Disaster Snapshot ==="
python3 "${ROOT_DIR}/scripts/backup.py" --db-path /var/lib/phoenix/phoenix.db --backup-dir /var/backups/phoenix

# STAGE 2: Note Data Counts
echo ""
echo "=== STAGE 2: Recording Pre-Disaster Census ==="
echo "Collecting baseline table counts from /var/lib/phoenix/phoenix.db:"
sqlite3 /var/lib/phoenix/phoenix.db "
SELECT 'users:       ', COUNT(*) FROM users UNION ALL
SELECT 'customers:   ', COUNT(*) FROM customers UNION ALL
SELECT 'services:    ', COUNT(*) FROM services UNION ALL
SELECT 'bookings:    ', COUNT(*) FROM bookings UNION ALL
SELECT 'invoices:    ', COUNT(*) FROM invoices;
"

# STAGE 3: Total Destruction
echo ""
echo "=== STAGE 3: Simulating Total Datacenter Destruction ==="
if [ "${TARGET_ENV}" = "aws" ]; then
    echo "[*] Triggering: terraform destroy -auto-approve"
    cd "${ROOT_DIR}/terraform/aws" && terraform destroy -auto-approve
elif [ "${TARGET_ENV}" = "virtualbox" ]; then
    echo "[*] Triggering: vagrant destroy -f"
    cd "${ROOT_DIR}/terraform/virtualbox" && vagrant destroy -f
fi
echo "[+] Target environment completely wiped out."

# STAGE 4: Re-provision Infrastructure
echo ""
echo "=== STAGE 4: Re-provisioning Infrastructure as Code ==="
if [ "${TARGET_ENV}" = "aws" ]; then
    echo "[*] Triggering: terraform apply -auto-approve"
    cd "${ROOT_DIR}/terraform/aws" && terraform apply -auto-approve
elif [ "${TARGET_ENV}" = "virtualbox" ]; then
    echo "[*] Triggering: vagrant up"
    cd "${ROOT_DIR}/terraform/virtualbox" && vagrant up
fi
echo "[+] Nodes online and reachable via SSH."

# STAGE 5: Ansible Disaster Recovery
echo ""
echo "=== STAGE 5: Executing Ansible Disaster Recovery Playbook ==="
cd "${ROOT_DIR}/ansible"
ansible-playbook -i inventory/hosts.ini playbooks/recover.yml

# STAGE 6: Puppet Baseline & Drift Reconciliation
echo ""
echo "=== STAGE 6: Enforcing Puppet Baseline Security & Nginx Configuration ==="
ssh -o StrictHostKeyChecking=no ubuntu@app.phoenix.local "sudo puppet agent -t || [ \$? -eq 2 ]"

# STAGE 7: Nagios Monitoring Recheck
echo ""
echo "=== STAGE 7: Verifying Nagios Monitoring Status ==="
python3 "${ROOT_DIR}/nagios/plugins/check_portal_health.py" -H 192.168.56.10 -p 8000

# STAGE 8: Post-Disaster Census Audit & Parity Assertion
echo ""
echo "=== STAGE 8: Executing Post-Disaster Audit ==="
python3 "${ROOT_DIR}/scripts/verify_recovery.py" --url http://192.168.56.10:8000 --db-path /var/lib/phoenix/phoenix.db

echo ""
echo "========================================================================"
echo "  [SUCCESS] DISASTER RECOVERY DRILL COMPLETED WITH 100% PARITY!"
echo "========================================================================"
