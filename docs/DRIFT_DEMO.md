# Phoenix Configuration Drift & Self-Healing Demonstration Runbook

This document describes how to execute and verify the **Self-Healing Configuration Drift Demonstration** on the `app-server` VM using Puppet.

---

## 1. Overview of Self-Healing Mechanism

In traditional systems, administrators make ad-hoc debugging fixes (e.g. stopping a service, loosening permissions to 0777, editing configuration files) that remain permanent and undetected.

In **Project Phoenix**:
1. **Puppet Master** holds the authoritative desired state for all nodes.
2. The **Puppet Agent** runs periodically on `app-server`.
3. If any file permission is modified, file content altered, or service stopped, Puppet automatically corrects the discrepancy and restores the baseline without human intervention.

---

## 2. Demonstration Procedure

### Step 1: Verify Initial Clean Baseline State
On `app-server`, run the Puppet agent:
```bash
sudo puppet agent -t
```

**Expected Output:**
```text
Info: Using environment 'production'
Info: Retrieving pluginfacts
Info: Retrieving plugin
Info: Loading facts
Info: Caching catalog for app-server
Info: Applying configuration version '1731737000'
Notice: Applied catalog in 0.42 seconds
```
*(Notice: No changes applied; machine is already in desired state).*

---

### Step 2: Inject Intentional Configuration Drift
Run the provided drift injection script on `app-server`:
```bash
bash /opt/phoenix/scripts/inject_drift.sh
```

**Expected Output:**
```text
==================================================
 Phoenix - Simulating Intentional System Drift
==================================================
[1/4] Tampering with /etc/phoenix-baseline.conf content...
      Appended unauthorized line to /etc/phoenix-baseline.conf
[2/4] Loosening file permissions to 0777 (Insecure)...
-rwxrwxrwx 1 root root 150 Nov 16 11:30 /etc/phoenix-baseline.conf
[3/4] Stopping Nginx web service...
      Nginx service is now STOPPED (Simulated outage)
[4/4] Current Drift Status Summary:
      - Service Nginx status: inactive
      - Permissions on /etc/phoenix-baseline.conf: 777
==================================================
 Drift successfully injected!
 Next step: Run 'sudo puppet agent -t' to trigger automated self-healing.
==================================================
```

---

### Step 3: Trigger Puppet Automated Self-Healing
Execute the Puppet agent to pull the catalog from Puppet Master:
```bash
sudo puppet agent -t
```

**Expected Output:**
```text
Info: Using environment 'production'
Info: Retrieving pluginfacts
Info: Retrieving plugin
Info: Loading facts
Info: Caching catalog for app-server
Info: Applying configuration version '1731737120'
--- /etc/phoenix-baseline.conf	2026-11-16 11:30:15.000000000 +0000
+++ /tmp/puppet-file20261116-2481-1b	2026-11-16 11:30:20.000000000 +0000
@@ -3,3 +3,2 @@
 SECURITY_COMPLIANCE=STRICT
 DRIFT_SELF_HEALING=ENABLED
-MALICIOUS_UNAUTHORIZED_OVERWRITE=TRUE
Notice: /Stage[main]/Phoenix::Baseline/File[/etc/phoenix-baseline.conf]/content: content changed '{sha256}e3b0c442...' to '{sha256}7a48d011...'
Notice: /Stage[main]/Phoenix::Baseline/File[/etc/phoenix-baseline.conf]/mode: mode changed '0777' to '0644'
Notice: /Stage[main]/Phoenix::Web/Service[nginx]/ensure: ensure changed 'stopped' to 'running'
Info: /Stage[main]/Phoenix::Web/Service[nginx]: Unscheduling refresh on Service[nginx]
Notice: Applied catalog in 1.84 seconds
```

**Key Self-Healing Actions Demonstrated:**
1. **Content Restoration**: Removed unauthorized string and reverted to declared checksum.
2. **Permission Hardening**: Restored file mode from `0777` back to secure `0644`.
3. **Service Recovery**: Detected stopped `nginx` daemon and restarted it to `running`.

---

### Step 4: Verify Idempotence (Second Run)
Immediately re-run Puppet agent on `app-server`:
```bash
sudo puppet agent -t
```

**Expected Output:**
```text
Info: Using environment 'production'
Info: Retrieving pluginfacts
Info: Retrieving plugin
Info: Loading facts
Info: Caching catalog for app-server
Info: Applying configuration version '1731737150'
Notice: Applied catalog in 0.38 seconds
```

**Result:** `0 changes`. Complete convergence and idempotency verified.
