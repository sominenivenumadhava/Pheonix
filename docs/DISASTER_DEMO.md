# Project Phoenix: Disaster Recovery Lifecycle Demonstration Runbook

This runbook guides operators, evaluators, and examiners through the complete, end-to-end Disaster Recovery as Code (DRaC) demonstration for **Project Phoenix**.

---

## 1. Executive Summary & Objectives

Project Phoenix demonstrates how a small business can survive a catastrophic datacenter or cloud failure with **sub-10 minute Recovery Time Objective (RTO)** and **zero committed transaction data loss (Recovery Point Objective - RPO)** using open-source DevOps tooling.

### Toolchain Responsibilities
| Tool | Core Responsibility in DR Workflow |
| :--- | :--- |
| **Terraform** | Provisions raw virtual infrastructure (VPC, Subnets, Security Groups, EC2 / VMs) from scratch in minutes. |
| **Ansible** | Automates post-provisioning software configuration, application deployment, and atomic database restoration. |
| **Puppet** | Enforces security baselines, manages system configuration, and continuously repairs configuration drift. |
| **Nagios Core** | Provides proactive 24/7 observability, detects service outages, and confirms recovery completion. |

---

## 2. Demonstration Architecture

```
[ Operator Workstation / Bastion ]
               │
   ┌───────────┼────────────────────────┐
   ▼           ▼                        ▼
[App Node]  [Puppet Master]      [Nagios Monitoring]
192.168.56.10 192.168.56.20       192.168.56.30
(FastAPI,    (Certificate CA,     (Core 4.5.1,
 Nginx,       Catalog Compiler,    Active Polling,
 SQLite DB)   Drift Auto-Heal)     Custom Plugins)
   ▲                                    │
   └──────── Active Probes (Health) ────┘
```

---

## 3. The 8-Stage Disaster Recovery Lifecycle

The demonstration executes an 8-stage sequence:

```
[1. Snapshot Backup] ──► [2. Pre-Disaster Census] ──► [3. Total Infrastructure Wipe]
                                                                  │
                                                                  ▼
[6. Puppet Drift Heal] ◄── [5. Ansible Recovery] ◄── [4. Terraform Re-provision]
         │
         ▼
[7. Nagios Green State] ──► [8. Post-Recovery Census & Parity Check]
```

---

## 4. Step-by-Step Execution Guide

### Mode A: VirtualBox Offline Lab (Recommended for Exam/Offline Demos)

#### Stage 1: Create Pre-Disaster Snapshot
On the **App Node** (or operator workstation):
```bash
python3 scripts/backup.py --db-path /var/lib/phoenix/phoenix.db --backup-dir /var/backups/phoenix
```
*Expected Output:*
```
[*] Starting backup from: /var/lib/phoenix/phoenix.db
[*] Destination: /var/backups/phoenix/phoenix_backup_YYYYMMDD_HHMMSS.db
[+] Snapshot created successfully.
[+] Integrity check: PASSED (PRAGMA integrity_check = ok)
[+] Logged entry into backup_records table.
```

> **Screenshot Checkpoint 1:** Terminal displaying the completed backup snapshot, SHA-256 hash, and `backup_records` log.

---

#### Stage 2: Pre-Disaster Census Audit
Capture baseline row counts:
```bash
sqlite3 /var/lib/phoenix/phoenix.db "
SELECT 'users:       ', COUNT(*) FROM users UNION ALL
SELECT 'customers:   ', COUNT(*) FROM customers UNION ALL
SELECT 'services:    ', COUNT(*) FROM services UNION ALL
SELECT 'bookings:    ', COUNT(*) FROM bookings UNION ALL
SELECT 'invoices:    ', COUNT(*) FROM invoices;
"
```
*Expected Output:*
```
users:        4
customers:    2
services:     4
bookings:     X
invoices:     Y
```

---

#### Stage 3: Catastrophic Infrastructure Destruction
Simulate total machine/datacenter loss:
```bash
cd terraform/virtualbox
vagrant destroy -f
```
*(If on AWS)*:
```bash
cd terraform/aws
terraform destroy -auto-approve
```
*Expected Result:*
- Virtual machines or EC2 instances are terminated.
- Nagios immediately transitions App Node services to `CRITICAL (Connection Refused / Host Unreachable)`.

> **Screenshot Checkpoint 2:** Nagios Web Dashboard (`http://192.168.56.30/nagios`) showing all App host services in red `CRITICAL` state.

---

#### Stage 4: Rapid Infrastructure Re-provisioning (IaC)
Recreate infrastructure automatically from code:
```bash
# VirtualBox:
cd terraform/virtualbox && vagrant up

# AWS:
cd terraform/aws && terraform apply -auto-approve
```
*Outcome:* Fresh virtual machines boot up with base operating systems, network interfaces, and SSH accessibility.

---

#### Stage 5: Ansible Disaster Recovery Execution
Deploy the application and restore the database from the external backup store:
```bash
cd ansible
ansible-playbook -i inventory/hosts.ini playbooks/recover.yml
```
*Key tasks executed:*
- Preflight checks (connectivity, Python, storage directory).
- App installation (Python venv, requirements, systemd unit, Nginx reverse proxy).
- Atomic restore: copies latest verified backup, invokes `scripts/restore.py`, performs `PRAGMA integrity_check`.
- Endpoint validation: queries `/health` and `/ready`.

> **Screenshot Checkpoint 3:** Ansible terminal output ending with `PLAY RECAP: app : ok=14 changed=9 unreachable=0 failed=0`.

---

#### Stage 6: Puppet Baseline & Drift Reconciliation
Ensure the rebuilt App node conforms to enterprise security baselines and reverses any manual drift:
```bash
ssh ubuntu@app.phoenix.local "sudo puppet agent -t"
```
*Expected Output:*
```
Info: Using configured environment 'production'
Info: Retrieving pluginfacts
Info: Retrieving plugin
Info: Loading facts
Info: Caching catalog for app.phoenix.local
Info: Applying configuration catalog
Notice: Applied catalog in 0.45 seconds
```

---

#### Stage 7: Nagios Monitoring Recheck
Verify that Nagios Core detects the recovered service and turns green:
```bash
# Execute plugin directly or wait for Nagios 60-second polling cycle:
python3 nagios/plugins/check_portal_health.py -H 192.168.56.10 -p 8000
```
*Expected Output:*
```
PORTAL OK - Status: healthy, DB: ok | response_time=0.012s;0.500;1.500;0;5.000
```

> **Screenshot Checkpoint 4:** Nagios dashboard displaying all hosts and services in green `OK` state.

---

#### Stage 8: Post-Disaster Census & Parity Check
Run the automated verification tool to assert 100% data integrity:
```bash
python3 scripts/verify_recovery.py --url http://192.168.56.10:8000 --db-path /var/lib/phoenix/phoenix.db
```
*Expected Output Table:*
```
CHECK ITEM                       | STATUS  | DETAILS
------------------------------------------------------------------------
API Health Probe (/health)       | PASS    | Latency: 12.4ms | status=healthy | db=ok
API Readiness Probe (/ready)     | PASS    | Latency: 8.1ms | ready=True
SQLite Physical Integrity        | PASS    | Integrity OK, FKs OK | Path: phoenix.db
Database Record Census           | PASS    | users:4, customers:2, services:4, bookings:X, invoices:Y
Recovery Event Logged            | PASS    | Inserted RECOVERY_VERIFIED row into recovery_events
------------------------------------------------------------------------
[>>>] FINAL VERDICT: RECOVERY SUCCESSFUL — ALL SYSTEMS FULLY OPERATIONAL
```

> **Screenshot Checkpoint 5:** Verification report table showing 100% PASS across all probes and identical pre/post record counts.

---

### Mode B: Automated Single-Command Runner
For evaluation testing or rehearsal on a single development workstation:
```bash
# Run complete lifecycle simulation:
python3 scripts/disaster_demo.py --mode local-simulate
```
This script automatically executes all 8 stages, calculates pre- and post-census comparisons, and prints the audit table.
