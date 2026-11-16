# Project Phoenix: 10-Minute Live Examination Demonstration Script

**Course:** INT333 (DevOps Advanced Configuration Management)  
**Project Title:** Disaster Recovery as Code for a Small Business with Self-Healing DevOps Automation  
**Total Target Duration:** 10 Minutes (600 Seconds)  

---

## Presentation Timeline Overview

```
[00:00 - 01:30]  Phase 1: Architecture & Technology Division of Labor (90s)
[01:30 - 03:00]  Phase 2: Live Portal & Baseline Monitoring State (90s)
[03:00 - 05:00]  Phase 3: Self-Healing Configuration Drift Demo (120s)
[05:00 - 08:00]  Phase 4: Full Catastrophic Disaster Recovery Demo (180s)
[08:00 - 09:30]  Phase 5: Post-Recovery Audit & 100% Data Parity Proof (90s)
[09:30 - 10:00]  Phase 6: Conclusion, RTO/RPO Summary & Q&A Transition (30s)
```

---

## Detailed Step-by-Step Script

### Minute 00:00 – 01:30 | Phase 1: Architecture & Purpose
**Speaker Narration:**
> *"Good morning, respected examiners. Today I present Project Phoenix: Disaster Recovery as Code for a Small Business with Self-Healing DevOps Automation. Small enterprises often cannot afford high-cost multi-region distributed databases. Phoenix solves this by combining four distinct DevOps tools into a synchronized lifecycle:
> 1. **Terraform** provisions our virtual infrastructure from code in under 3 minutes.
> 2. **Ansible** deploys our application stack and orchestrates automated disaster recovery.
> 3. **Puppet** runs as a declarative agent continuously repairing unauthorized configuration drift.
> 4. **Nagios Core** monitors all nodes and services with custom probes to detect outages.
> Our application tier is a modern FastAPI backend with SQLite in WAL mode, backed by a React TypeScript portal."*

**Visual Action:**
- Show `ARCHITECTURE.md` topology diagram or system slide displaying the 4 nodes.

---

### Minute 01:30 – 03:00 | Phase 2: Live Baseline Operations
**Speaker Narration:**
> *"Let us first verify that all systems are operational under normal baseline conditions. I will open the Phoenix Business Portal in the browser and show our Nagios Core monitoring dashboard."*

**Terminal Command:**
```bash
# Verify backend and database health
curl -s http://192.168.56.10:8000/health | jq .
```
*Expected Output:*
```json
{
  "status": "healthy",
  "database": "ok",
  "timestamp": "2026-11-16T11:40:00Z"
}
```

**Visual Action:**
1. Open browser tab 1: `http://192.168.56.10` (Login as `admin@phoenix.local` / `AdminPass123!`).
2. Show Services, Bookings, and System Status page.
3. Open browser tab 2: `http://192.168.56.30/nagios` (Nagios Service Status: All 12 services in green `OK` status).

---

### Minute 03:00 – 05:00 | Phase 3: Self-Healing Configuration Drift Demo
**Speaker Narration:**
> *"Now we demonstrate Puppet's self-healing automation. In real life, a rogue administrator or attacker might tamper with a configuration file or disable Nginx. I will manually inject drift by modifying the Nginx site configuration, corrupting permissions, and stopping Nginx."*

**Terminal Commands on App Node:**
```bash
# 1. Inject configuration drift and stop service
sudo sed -i 's/8000/9999/g' /etc/nginx/sites-available/phoenix
sudo chmod 777 /var/lib/phoenix/phoenix.db
sudo systemctl stop nginx
sudo systemctl status nginx --no-pager
```

**Speaker Narration:**
> *"Notice Nginx is now dead and the configuration is corrupted. Now, instead of human intervention, we invoke Puppet to enforce the declarative desired state catalog."*

**Terminal Command on App Node:**
```bash
sudo puppet agent -t
```
*Expected Output:*
```
Notice: /Stage[main]/Phoenix::Web/File[/etc/nginx/sites-available/phoenix]/content: content changed ...
Notice: /Stage[main]/Phoenix::Baseline/File[/var/lib/phoenix/phoenix.db]/mode: mode changed to '0660'
Notice: /Stage[main]/Phoenix::Web/Service[nginx]/ensure: ensure changed 'stopped' to 'running'
Notice: Applied catalog in 0.48 seconds
```

**Speaker Narration:**
> *"Puppet detected the drift, restored the template from source control, fixed the file permissions back to 0660, and restarted Nginx. Let us verify Nginx is active again."*

```bash
sudo systemctl is-active nginx
# Output: active
```

---

### Minute 05:00 – 08:00 | Phase 4: Full Catastrophic Disaster Recovery
**Speaker Narration:**
> *"Now for the core capability of Phoenix: Catastrophic Disaster Recovery. We will take a live transaction snapshot, note our record counts, wipe the entire infrastructure to simulate datacenter loss, and recover."*

**Step 1: Backup Now & Note Census**
```bash
python3 scripts/backup.py --db-path /var/lib/phoenix/phoenix.db --backup-dir /var/backups/phoenix
sqlite3 /var/lib/phoenix/phoenix.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM services;"
```

**Step 2: Destroy Infrastructure (Catastrophic Loss)**
```bash
cd terraform/virtualbox
vagrant destroy -f app
# (Or on AWS: cd terraform/aws && terraform destroy -auto-approve)
```

**Speaker Narration:**
> *"The application server is now destroyed. If we inspect Nagios, within seconds the probe turns to CRITICAL red. Now, we initiate our Disaster Recovery as Code pipeline."*

**Visual Action:**
- Show Nagios Web GUI turning red (`CRITICAL: Connection refused`).

**Step 3: Re-provision Infrastructure**
```bash
vagrant up app
# (Or on AWS: terraform apply -auto-approve)
```

**Step 4: Execute Ansible Recovery Playbook**
```bash
cd ansible
ansible-playbook -i inventory/hosts.ini playbooks/recover.yml
```

**Speaker Narration:**
> *"Ansible connects to the newly booted VM, provisions the virtual environment, restores the database from our off-site backup repository, runs the integrity checks, and starts the systemd service."*

---

### Minute 08:00 – 09:30 | Phase 5: Verification & 100% Data Parity
**Speaker Narration:**
> *"The recovery playbook has completed. Now we execute our automated verification engine to mathematically prove zero data loss and complete operational readiness."*

**Terminal Command:**
```bash
python3 scripts/verify_recovery.py --url http://192.168.56.10:8000 --db-path /var/lib/phoenix/phoenix.db
```
*Expected Output:*
```
========================================================================
      PHOENIX DISASTER RECOVERY AS CODE — VERIFICATION REPORT
========================================================================
CHECK ITEM                       | STATUS  | DETAILS
------------------------------------------------------------------------
API Health Probe (/health)       | PASS    | Latency: 12.1ms | status=healthy | db=ok
API Readiness Probe (/ready)     | PASS    | Latency: 7.9ms | ready=True
SQLite Physical Integrity        | PASS    | Integrity OK, FKs OK | Path: phoenix.db
Database Record Census           | PASS    | users:4, customers:2, services:4, bookings:0, invoices:0
Recovery Event Logged            | PASS    | Inserted RECOVERY_VERIFIED row into recovery_events
------------------------------------------------------------------------
[>>>] FINAL VERDICT: RECOVERY SUCCESSFUL — ALL SYSTEMS FULLY OPERATIONAL
========================================================================
```

**Visual Action:**
- Show Nagios dashboard turning back to green `OK`.
- Open portal in browser and refresh: User is logged in and all services are visible.

---

### Minute 09:30 – 10:00 | Phase 6: Conclusion & Examiner Q&A
**Speaker Narration:**
> *"To summarize our results:
> - **RTO:** Under 7 minutes from total node destruction to full service availability.
> - **RPO:** Zero committed transaction data loss, mathematically verified across all 7 relational tables.
> - **Self-Healing:** Configuration drift automatically repaired in 0.48 seconds.
> All code is idempotent, infrastructure is disposable, and all disaster recovery workflows are version-controlled. Thank you, and I am now ready for questions."*
