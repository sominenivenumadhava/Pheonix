# Project Phoenix: Troubleshooting & Incident Remediation Guide

**Course:** INT333 (DevOps Advanced Configuration Management)  
**Scope:** Terraform, Ansible, Puppet, Nagios, SQLite, FastAPI, and Frontend  

---

## 1. Quick Diagnostic Triage Matrix

| Symptom / Error Message | Suspect Component | Immediate Diagnostic Command |
| :--- | :--- | :--- |
| `Connection refused on port 8000 / 80` | App Service / Nginx | `sudo systemctl status phoenix-backend nginx` |
| `certificate verify failed` | Puppet Master / Agent CA | `sudo /opt/puppetlabs/bin/puppetserver ca list --all` |
| `sqlite3.OperationalError: database is locked` | SQLite Concurrent Writes | `sqlite3 /var/lib/phoenix/phoenix.db "PRAGMA journal_mode;"` |
| `Return code of 127 is out of bounds` | Nagios Libexec Plugin Path | `ls -l /usr/local/nagios/libexec/check_portal_health.py` |
| `Host key verification failed` | Ansible SSH Key Host Fingerprint | `ssh-keygen -R <host_ip>` |
| `Total Errors: > 0` | Nagios Configuration Verification | `/usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg` |

---

## 2. Infrastructure as Code (Terraform) Issues

### Issue 2.1: Terraform AWS Credential Error
- **Symptom:** `Error: No valid credential sources found for AWS Provider`.
- **Root Cause:** AWS CLI environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are unset or expired.
- **Fix:**
  ```bash
  aws configure
  # Or export temporary credentials:
  export AWS_ACCESS_KEY_ID="AKIA..."
  export AWS_SECRET_ACCESS_KEY="..."
  export AWS_DEFAULT_REGION="us-east-1"
  ```

### Issue 2.2: VirtualBox / Vagrant Host-Only Network Collision
- **Symptom:** `The specified host-only network does not exist: 'vboxnet0'`.
- **Root Cause:** VirtualBox default host-only network was removed or named differently (e.g., `VirtualBox Host-Only Ethernet Adapter` on Windows).
- **Fix:**
  Edit `terraform/virtualbox/Vagrantfile` or re-create the network interface:
  ```bash
  vboxmanage hostonlyif create
  vboxmanage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0
  ```

---

## 3. Configuration & Deployment (Ansible) Issues

### Issue 3.1: SSH "Host Key Verification Failed"
- **Symptom:** `UNREACHABLE! => {"changed": false, "msg": "Host key verification failed."}`.
- **Root Cause:** Recreated VM has a new SSH host key that conflicts with your existing `~/.ssh/known_hosts`.
- **Fix:**
  Remove the stale host key or enable host key checking bypass in Ansible:
  ```bash
  ssh-keygen -f "~/.ssh/known_hosts" -R "192.168.56.10"
  # Or run ansible with the env var:
  ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i inventory/hosts.ini playbooks/site.yml
  ```

### Issue 3.2: Ansible Vault Decryption Failed
- **Symptom:** `Decryption failed (no vault secrets found that can decrypt)`.
- **Root Cause:** The vault secret was encrypted with a password not provided at runtime.
- **Fix:**
  Always provide the vault password file or interactive prompt:
  ```bash
  ansible-playbook -i inventory/hosts.ini playbooks/site.yml --ask-vault-pass
  # Or using password file:
  ansible-playbook -i inventory/hosts.ini playbooks/site.yml --vault-password-file ~/.phoenix_vault_pass
  ```

### Issue 3.3: Apt Lock Contention
- **Symptom:** `Could not get lock /var/lib/dpkg/lock-frontend`.
- **Root Cause:** Ubuntu background `unattended-upgrades` is holding the apt lock immediately after fresh VM boot.
- **Fix:**
  Wait 60 seconds or terminate unattended upgrades:
  ```bash
  sudo systemctl stop unattended-upgrades
  sudo killall apt apt-get 2>/dev/null || true
  ```

---

## 4. State Enforcement & Drift (Puppet) Issues

### Issue 4.1: Certificate Verification Mismatch
- **Symptom:** `SSL_connect returned=1 errno=0 state=error: certificate verify failed [certificate signature failure]`.
- **Root Cause:** The App VM was rebuilt, but the Puppet Master CA still holds the old SSL certificate for `app.phoenix.local`.
- **Fix:**
  On the **Puppet Master**:
  ```bash
  sudo /opt/puppetlabs/bin/puppetserver ca clean --certname app.phoenix.local
  ```
  On the **App Node**:
  ```bash
  sudo rm -rf /etc/puppetlabs/puppet/ssl
  sudo puppet agent -t --server puppet.phoenix.local
  ```
  On the **Puppet Master**:
  ```bash
  sudo /opt/puppetlabs/bin/puppetserver ca sign --certname app.phoenix.local
  ```

### Issue 4.2: Puppet Master Out of Memory (OOM)
- **Symptom:** `puppetserver.service failed with exit code 143 (SIGTERM)`.
- **Root Cause:** The default JVM heap allocation is 2GB, exceeding available VM memory on small nodes.
- **Fix:**
  Edit `/etc/default/puppetserver` and adjust JVM heap:
  ```bash
  JAVA_ARGS="-Xms768m -Xmx768m"
  sudo systemctl restart puppetserver
  ```

---

## 5. Continuous Monitoring (Nagios) Issues

### Issue 5.1: Plugin Returns 127 (Exec File Not Found / Permission Denied)
- **Symptom:** `(Return code of 127 is out of bounds - plugin may be missing)`.
- **Root Cause:** Plugin file is missing executable bit (`chmod +x`), has incorrect path in `commands.cfg`, or has a missing Python interpreter shebang.
- **Fix:**
  ```bash
  sudo chmod +x /usr/local/nagios/libexec/check_portal_health.py
  # Verify direct execution as nagios user:
  sudo -u nagios /usr/local/nagios/libexec/check_portal_health.py -H 192.168.56.10 -p 8000
  ```

### Issue 5.2: False-Positive CRITICAL Alerts Due to Latency
- **Symptom:** `PORTAL CRITICAL - Health check failed: timed out`.
- **Root Cause:** The default probe timeout (5.0s) was exceeded during high VM CPU load.
- **Fix:**
  Adjust the `-w` (warning) and `-c` (critical) thresholds or `--timeout` in `nagios/etc/commands.cfg`:
  ```ini
  command_line    $USER1$/check_portal_health.py -H $HOSTADDRESS$ -p $ARG1$ -w 1.0 -c 3.0 -t 8.0
  ```
  Reload Nagios: `sudo systemctl reload nagios`.

---

## 6. Storage & Database (SQLite) Issues

### Issue 6.1: Database Is Locked (`SQLITE_BUSY`)
- **Symptom:** `sqlite3.OperationalError: database is locked`.
- **Root Cause:** Multiple concurrent processes attempting writes while journaling is set to `DELETE` mode instead of `WAL` mode.
- **Fix:**
  Confirm WAL mode is enabled:
  ```bash
  sqlite3 /var/lib/phoenix/phoenix.db "PRAGMA journal_mode=WAL;"
  sqlite3 /var/lib/phoenix/phoenix.db "PRAGMA busy_timeout=5000;"
  ```

### Issue 6.2: Restored Database Fails Integrity Check
- **Symptom:** `PRAGMA integrity_check;` returns `*** in database main *** Page X: ... corrupted`.
- **Root Cause:** Snapshot was copied mid-write without using the atomic backup API, or file transfer was truncated.
- **Fix:**
  1. Do not use direct raw file copies while writes are active.
  2. Restore using `scripts/restore.py`, which validates the backup file checksum *before* deploying.
  3. If primary is corrupted, restore from the penultimate backup file:
     ```bash
     python3 scripts/restore.py --backup-file /var/backups/phoenix/phoenix_backup_PENULTIMATE.db
     ```

---

## 7. Application & Frontend Issues

### Issue 7.1: Port 8000 Already in Use
- **Symptom:** `[Errno 98] Address already in use` or `[Errno 10048]`.
- **Root Cause:** A orphaned Uvicorn process is still listening on port 8000.
- **Fix:**
  ```bash
  # Linux:
  sudo fuser -k 8000/tcp
  # Windows PowerShell:
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
  ```

### Issue 7.2: Token Expired / 401 Unauthorized
- **Symptom:** UI displays "Unauthorized: Invalid or expired token" and redirects to login.
- **Root Cause:** Short-lived JWT has exceeded its 60-minute expiration lifespan.
- **Fix:**
  Log in again via `/auth/login` to obtain a fresh Bearer token.
