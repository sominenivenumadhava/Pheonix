# Project Phoenix: Standard Operating Procedure — Disaster Recovery (SOP-DR-01)

**Classification:** Operational Runbook  
**Target Audience:** On-call DevOps Engineers, System Administrators, Evaluators  
**Applies to:** Production, Staging, and Educational Simulation Lab  

---

## 1. Purpose & Incident Scope

This Standard Operating Procedure defines the exact steps required to execute a full disaster recovery operation for the Phoenix Small Business Portal following a catastrophic outage.

### Qualifying Incident Triggers (When to Declare Disaster)
Execute this procedure if **any** of the following conditions persist for > 3 minutes:
1. **Total Hardware or Hypervisor Crash:** VirtualBox host crash or AWS EC2 instance termination.
2. **Unrecoverable File System Corruption:** SQLite database file destroyed or failing `PRAGMA integrity_check`.
3. **Compromised Host / Security Breach:** System tampering where clean re-provisioning is required.
4. **Cloud Datacenter Availability Zone Outage:** AWS AZ loss requiring instant spin-up in an alternate AZ or local lab.

---

## 2. Roles & Communication Protocol

| Role | Primary Responsibility | Action Channel |
| :--- | :--- | :--- |
| **Incident Commander (IC)** | Declares disaster, coordinates timeline, logs PIR | Emergency Bridge |
| **DevOps Operator** | Executes Terraform, Ansible, and Puppet commands | CLI / Bastion Node |
| **Observability Lead** | Monitors Nagios state transitions, validates metrics | Nagios Web GUI |

---

## 3. Step-by-Step Recovery Procedure

```
[Phase 1: Alert Triage]
         │ Nagios CRITICAL Alert
         ▼
[Phase 2: Disaster Declaration]
         │ Total node failure confirmed
         ▼
[Phase 3: Infrastructure Re-provisioning]
         │ Terraform / Vagrant apply
         ▼
[Phase 4: Ansible Deployment & DB Restore]
         │ ansible-playbook recover.yml
         ▼
[Phase 5: Puppet Drift & Security Baseline]
         │ puppet agent -t
         ▼
[Phase 6: End-to-End Health & Parity Verification]
         │ verify_recovery.py
         ▼
[Phase 7: Sign-off & Incident Closure]
```

---

### Phase 1: Incident Detection & Outage Verification
1. Nagios alerts with `CRITICAL: HTTP Connection Refused` or `CRITICAL: Socket Timeout`.
2. Inspect the Nagios Service Details:
   - URL: `http://192.168.56.30/nagios`
   - Check `Phoenix_Portal_Health` and `Phoenix_Nginx_HTTP`.
3. Attempt emergency SSH login to App Node:
   ```bash
   ssh -o ConnectTimeout=5 ubuntu@192.168.56.10
   ```
4. If the host is unreachable or the disk is corrupted, proceed to Phase 2.

---

### Phase 2: Declare Disaster & Prepare Backup Store
1. Confirm that external backups exist in the off-host backup repository:
   ```bash
   ls -la /var/backups/phoenix/*.db
   ```
2. Identify the most recent snapshot file:
   ```bash
   LATEST_BACKUP=$(ls -t /var/backups/phoenix/phoenix_backup_*.db | head -1)
   echo "Targeting snapshot: ${LATEST_BACKUP}"
   ```

---

### Phase 3: Infrastructure Re-provisioning (IaC)

#### Option A: VirtualBox Environment (Offline Lab)
```bash
cd terraform/virtualbox
# If cleaning up a crashed VM:
vagrant destroy -f app
# Spin up clean replacement VM:
vagrant up app
```

#### Option B: AWS Environment (Cloud Deployment)
```bash
cd terraform/aws
# Clean up terminated / corrupted instances:
terraform apply -auto-approve
```
*Verification:* Confirm new VM or instance responds to SSH:
```bash
ssh ubuntu@192.168.56.10 "echo 'Node online'"
```

---

### Phase 4: Application Deployment & Data Restoration (Ansible)
Execute the emergency recovery playbook from the Control Node:
```bash
cd ansible
ansible-playbook -i inventory/hosts.ini playbooks/recover.yml
```

#### What `recover.yml` Executes Automatically:
1. **Pre-flight Checks:** Verifies SSH access, target directories, and external backup file existence.
2. **App Deployment:** Deploys Python 3.12 virtualenv, dependencies, systemd unit, and Nginx proxy.
3. **Database Restore:**
   - Transmits the latest verified backup file to `/var/lib/phoenix/phoenix.db`.
   - Runs `scripts/restore.py` which validates SHA-256 and executes `PRAGMA integrity_check`.
   - Updates `backup_records` marking `restore_verified = 1`.
   - Records `DATABASE_RESTORE` event in `recovery_events`.
4. **Service Startup:** Starts `phoenix-backend` and reloads Nginx.
5. **Endpoint Validation:** Performs internal HTTP GET on `/health` and `/ready`.

---

### Phase 5: Puppet Baseline Enforcement & Drift Reconciliation
Connect to the recovered node to enforce security policies and remove any unauthorized temporary artifacts:
```bash
ssh ubuntu@192.168.56.10 "sudo puppet agent -t"
```
*Expected Return Code:*
- `0`: Catalog applied cleanly with 0 changes.
- `2`: Catalog applied cleanly with corrective changes.
*(Both indicate success).*

---

### Phase 6: Post-Recovery Health & Data Census Verification
Execute the automated recovery verification tool:
```bash
python3 scripts/verify_recovery.py --url http://192.168.56.10:8000 --db-path /var/lib/phoenix/phoenix.db
```

#### Acceptance Criteria for Operational Sign-off:
- [x] `/health` returns HTTP 200 with `status: healthy` and `database: ok`.
- [x] `/ready` returns HTTP 200 with `ready: True`.
- [x] `PRAGMA integrity_check` returns `ok`.
- [x] Table census shows 100% row match with pre-disaster state.
- [x] New `RECOVERY_VERIFIED` event is logged in `recovery_events`.

---

### Phase 7: Nagios State Normalization & Incident Closure
1. Check the Nagios dashboard (`http://192.168.56.30/nagios`).
2. Force an immediate service check of `Phoenix_Portal_Health`:
   - Service state transitions from `CRITICAL` -> `OK`.
3. If scheduled downtime was enabled during the outage, cancel downtime.
4. Export the `recovery_events` table for the Post-Incident Review (PIR):
   ```bash
   sqlite3 /var/lib/phoenix/phoenix.db -header -column "SELECT * FROM recovery_events ORDER BY id DESC LIMIT 5;"
   ```
5. Declare incident resolved.
