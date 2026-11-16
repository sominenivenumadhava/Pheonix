# Phoenix Nagios Observability & Disaster Recovery Demonstration Runbook

This runbook details the exact operational workflow to demonstrate continuous monitoring, alert lifecycle handling (OK $\to$ CRITICAL $\to$ Acknowledgement $\to$ Scheduled Downtime $\to$ Restoration $\to$ OK), and custom plugin validation during the project viva and practical evaluation.

---

## 1. Accessing the Nagios Core Dashboard

- **URL**: `http://192.168.56.40/nagios/` (or `http://localhost:8088/nagios/` if using port forwarding)
- **Username**: `nagiosadmin`
- **Password**: `AdminPass123!` (or password configured during `install_nagios.sh`)

Navigate to **Current Status** $\to$ **Services** in the left sidebar to view the real-time matrix of monitored services.

---

## 2. Step-by-Step Demonstration Workflow

### Step 1: Baseline Healthy State (All Services OK)
1. In the Nagios Web UI, inspect the host `app-server`.
2. Confirm the following custom and standard services are in the green **OK** state:
   - `Portal Health & Latency`: Status Information reports:  
     `PORTAL HEALTH OK - HTTP 200, status=healthy, db=ok (42.5ms, v=1.0.0)`
   - `HTTP Web Server`: `HTTP OK - HTTP/1.1 200 OK`
   - `Nginx HTTP 5xx Errors`: `WEB ERRORS OK - Found 0 HTTP 5xx errors`

> **[SCREENSHOT POINT 1 - BASELINE HEALTHY STATE]**  
> *Capture the Nagios Services Overview screen showing all hosts (app-server, puppet-master, nagios-server) and services with green "OK" badges.*

---

### Step 2: Trigger Simulated Service Failure
On the `app-server` terminal, execute the failure simulator script:
```bash
bash /opt/phoenix/scripts/simulate_failure.sh
```

**Expected Console Output:**
```text
==================================================
 Phoenix Disaster Simulation - Application Failure
==================================================
[+] Stopped systemd service 'phoenix-backend'.
[+] Successfully logged 'SERVICE_FAILURE' in recovery_events table.
==================================================
 Status: Application service stopped.
 Expected Nagios status: CRITICAL (Connection refused on /health)
==================================================
```

---

### Step 3: Observe Failure Detection in Nagios
1. Within 60 seconds (or click **Re-schedule the next check of this service** $\to$ **Commit** to force an immediate check):
2. The service `Portal Health & Latency` transitions to red **CRITICAL**.
3. Status Information displays:
   ```text
   PORTAL HEALTH CRITICAL - Connection refused or host unreachable: [Errno 111] Connection refused | 'time'=1.2ms;500.0;1500.0;0;
   ```

> **[SCREENSHOT POINT 2 - FAILURE ALERT STATE]**  
> *Capture the red CRITICAL state for "Portal Health & Latency" showing the connection refused status message and performance data.*

---

### Step 4: Operator Acknowledgement of Incident
1. Click on the hyperlinked service description: **Portal Health & Latency**.
2. Under **Service Commands** in the right panel, click **Acknowledge this service problem**.
3. Enter comment:
   `Investigating total portal failure under incident ticket INC-2026-DR01.`
4. Ensure **Send Notification** is checked. Click **Commit**.
5. Return to the Services view: A small sticky-note icon appears next to the CRITICAL badge indicating the incident is actively owned.

> **[SCREENSHOT POINT 3 - OPERATOR ACKNOWLEDGEMENT]**  
> *Capture the service detail page showing the entered acknowledgement comment and user credentials.*

---

### Step 5: Schedule Planned Maintenance Downtime
1. Under **Service Commands**, click **Schedule downtime for this service**.
2. Set duration: **30 minutes**.
3. Comment:
   `Scheduled maintenance: Rebuilding service and restoring database backup.`
4. Click **Commit**.
5. Return to Services view: A small wrench icon appears next to the service, preventing further alert notifications during the repair window.

> **[SCREENSHOT POINT 4 - SCHEDULED DOWNTIME]**  
> *Capture the Service state displaying the scheduled downtime indicator icon.*

---

### Step 6: Execute Restoration (Self-Healing or Ansible DR)

#### Option A: Quick Service Self-Healing via Puppet
On `app-server`:
```bash
sudo puppet agent -t
```
*(Puppet detects the stopped `nginx` or backend configuration and restarts the service).*

#### Option B: Full Disaster Recovery via Ansible
From `control-node`:
```bash
cd /opt/phoenix/ansible
ansible-playbook -i inventory/hosts.ini playbooks/recover.yml
```
*(Ansible runs preflight checks, restores the latest verified database snapshot from `/var/backups/phoenix-db/`, and restarts `phoenix-backend`).*

---

### Step 7: Proof of Recovery & Return to OK State
1. In the Nagios Web UI, click **Re-schedule the next check of this service** $\to$ **Commit**.
2. The check executes `check_portal_health.py`:
   - Returns exit code `0`.
   - Status transitions back to green **OK**.
   - Acknowledgement and downtime are automatically fulfilled.
3. The business portal is certified healthy.

> **[SCREENSHOT POINT 5 - VERIFIED RECOVERY GREEN STATE]**  
> *Capture the Nagios dashboard returning to green OK status, proving end-to-end recovery verification.*
