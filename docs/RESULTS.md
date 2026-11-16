# PHOENIX: Test, Execution & Verification Log (RESULTS.md)

This document is the single source of truth for all test executions, demonstrations, and operational checks for Project **PHOENIX**.
Per project rules:
- **No invented results**: Only tests and commands physically executed are marked as PASSED.
- **Unrun tests**: Any test or operational check that cannot be run in the current environment is explicitly listed as **NOT RUN** with the exact technical reason.

---

## 1. Test Execution Summary

| Phase / Component | Total Checks | Passed | Failed | Not Run | Status |
|---|---|---|---|---|---|
| **Phase 0: Repo Skeleton** | 3 | 3 | 0 | 0 | Completed |
| **Day 1: Backend & DB** | 32 | 32 | 0 | 0 | Completed |
| **Day 2: Frontend & Ansible** | 10 | 9 | 0 | 1 | Completed |
| **Day 3: Terraform & Puppet** | 7 | 5 | 0 | 2 | Completed |
| **Day 4: Nagios & Observability** | 11 | 10 | 0 | 1 | Completed |
| **Day 5: Final Viva & DR Run** | 0 | 0 | 0 | 0 | Pending |

---

## 2. Detailed Execution Log

### Phase 0: Repository Skeleton & Governance
*Summary: 3 checks executed, 3 PASSED.*

### Day 1: Backend, Database, Auth & Operational Verification
*Summary: 32 checks executed, 32 PASSED (FastAPI, SQLite, 29/29 pytest test cases, backup and restore on disposable database).*

### Day 2: Frontend (Vite + React) & Ansible Automation
*Summary: 9 checks executed, 9 PASSED (7 Vitest tests, Vite production build, PyYAML syntax validation).*

### Day 3: Terraform Infrastructure as Code & Puppet Self-Healing
*Summary: 5 checks executed, 5 PASSED (terraform fmt, init, validate, workspaces, plan dry-run).*

### Day 4: Nagios Core, Custom Plugins & Alert Lifecycle
**Execution Timestamp**: 2026-11-16 11:30:55 IST  
**Environment**: Python 3.12.9, pytest 9.2.0, platform Windows 11  

| Check ID | Component / Target | Test Name / Command | Result | Evidence / Details |
|---|---|---|---|---|
| **D4-CHK-01** | Plugin 1: Healthy | `test_nagios_plugins.py::test_portal_health_ok` | **PASSED** | Exit 0: `PORTAL HEALTH OK - HTTP 200, status=healthy, db=ok` |
| **D4-CHK-02** | Plugin 1: Latency Warning | `test_nagios_plugins.py::test_portal_health_warning_slow` | **PASSED** | Exit 1: `PORTAL HEALTH WARNING - Response time 203.0ms exceeds warning threshold 80.0ms` |
| **D4-CHK-03** | Plugin 1: DB Failed | `test_nagios_plugins.py::test_portal_health_critical_db_down` | **PASSED** | Exit 2: `PORTAL HEALTH CRITICAL - HTTP 503 (Service Unavailable)` |
| **D4-CHK-04** | Plugin 1: Service Down | `test_nagios_plugins.py::test_portal_health_critical_connection_refused` | **PASSED** | Exit 2: `PORTAL HEALTH CRITICAL - Connection refused or host unreachable` |
| **D4-CHK-05** | Plugin 1: High Latency | `test_nagios_plugins.py::test_portal_health_critical_latency` | **PASSED** | Exit 2: `PORTAL HEALTH CRITICAL - Response time 229.0ms exceeds critical threshold 100.0ms` |
| **D4-CHK-06** | Plugin 2: Zero 5xx Errors | `test_nagios_plugins.py::test_web_errors_ok` | **PASSED** | Exit 0: `WEB ERRORS OK - Found 0 HTTP 5xx errors in last 5m` |
| **D4-CHK-07** | Plugin 2: Warning Spikes | `test_nagios_plugins.py::test_web_errors_warning` | **PASSED** | Exit 1: `WEB ERRORS WARNING - Found 7 HTTP 5xx errors in last 5m (threshold >= 5)` |
| **D4-CHK-08** | Plugin 2: Critical Spikes | `test_nagios_plugins.py::test_web_errors_critical` | **PASSED** | Exit 2: `WEB ERRORS CRITICAL - Found 25 HTTP 5xx errors in last 5m (threshold >= 20)` |
| **D4-CHK-09** | Plugin 2: Missing Log File | `test_nagios_plugins.py::test_web_errors_unknown_missing_file` | **PASSED** | Exit 3: `WEB ERRORS UNKNOWN - Log file does not exist` |
| **D4-CHK-10** | Config Validation | `python nagios/validate_config.py` | **PASSED** | Verified 3 Hosts, 12 Services, 9 Commands with 0 syntax or reference errors |
| **D4-CHK-11** | Nagios Core Verification | `nagios -v /usr/local/nagios/etc/nagios.cfg` | **NOT RUN** | Nagios binary must be executed on Ubuntu `nagios-server` VM. Handled via `install_nagios.sh`. |

---

## 3. Environment Limitations & Unrun Items Log

| Date | Target Subsystem | Intended Check | Reason for Not Running | Remediation / Next Action |
|---|---|---|---|---|
| 2026-11-16 | Nagios Core Daemon | `nagios -v /usr/local/nagios/etc/nagios.cfg` | Nagios Core C-daemon is compiled for Linux. | Python object validator passed with 0 errors. Executed automatically during `bash nagios/install_nagios.sh` on VM. |
| 2026-11-16 | AWS Infrastructure | `terraform apply` on AWS | Awaiting user instructions and active AWS session credentials. | Verified via `terraform validate` and `terraform init`. Apply when AWS keys are exported. |
| 2026-11-16 | Ansible VM Run | `ansible-playbook -i inventory/hosts.ini site.yml` | Windows OS does not support native Ansible control node engine. | Detailed manual runbook provided in `docs/VIRTUALBOX_LAB_SETUP.md` for execution on Ubuntu control node. |
| 2026-11-16 | Puppet Master/Agent | `puppet parser validate` and `puppet agent -t` | Puppet Server & Agent require Linux VM environment. | Full setup guide in `docs/PUPPET_SETUP_GUIDE.md` and drift demonstration script in `scripts/inject_drift.sh`. |
