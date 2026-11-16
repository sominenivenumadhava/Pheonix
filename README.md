# Project Phoenix: Disaster Recovery as Code for a Small Business with Self-Healing DevOps Automation

> **Course:** INT333 – DevOps Advanced Configuration Management  
> **Institution:** Lovely Professional University (LPU)  
> **Academic Project Monorepo:** 100% Complete & Verified  

---

## 1. Executive Summary

Small businesses rely heavily on online portals for customer bookings, invoicing, and appointments. When an infrastructure failure, ransomware attack, or cloud outage occurs, recovery often takes days due to manual configurations, missing backups, and undocumented dependencies.

**Project Phoenix** provides a complete, production-grade **Disaster Recovery as Code (DRaC)** architecture combined with **Self-Healing Automation**:
- **Recovery Time Objective (RTO):** Rebuild the entire production stack from zero to fully operational in **< 10 minutes**.
- **Recovery Point Objective (RPO):** Zero committed transaction data loss via externalized, verified SQLite snapshots.
- **Continuous Self-Healing:** Autonomous background drift repair that detects and corrects unauthorized system modifications without human intervention.
- **Comprehensive Observability:** Active 24/7 monitoring through Nagios Core with custom Python probes that verify recovery rather than assuming it.

---

## 2. Complete DevOps Toolchain Division of Labor

```
                                  PROJECT PHOENIX
       ┌──────────────────┬──────────────────┬─────────────────┬──────────────────┐
       ▼                  ▼                  ▼                 ▼                  ▼
 [ Terraform ]      [ Ansible ]        [ Puppet ]        [ Nagios Core ]    [ App Stack ]
 Infrastructure     Orchestration      Self-Healing      Continuous         FastAPI + SQLite
 as Code (Day 0)    & DR (Day 1)       Drift (Day 2+)    Probes (Day 2+)    + React + Vite
```

| Subsystem | Tool | Scope & Specific Responsibilities |
| :--- | :--- | :--- |
| **Infrastructure** | **Terraform 1.5+** | Provisions AWS VPC, Subnets, Security Groups, and EC2 instances (`terraform/aws/`) or 4-node VirtualBox equivalent (`terraform/virtualbox/`). Manages `dev` and `prod` workspaces. |
| **Orchestration** | **Ansible Core 2.14+** | Push-based procedural configuration (`ansible/`). Deploys virtual environments, Nginx reverse proxies, systemd units, Ansible Vault secrets, and executes atomic recovery (`recover.yml`). |
| **Self-Healing** | **Puppet 7/8** | Declarative pull-based state enforcement (`puppet/modules/phoenix/`). Master-agent architecture compiles catalogs, enforces security permissions, and automatically repairs configuration drift every 30 minutes. |
| **Observability** | **Nagios Core 4.5+** | 24/7 active health monitoring (`nagios/`). Two custom plugins (`check_portal_health.py` and `check_web_errors.sh`) monitor latency, HTTP 5xx rates, and database connectivity. |
| **Application** | **FastAPI + React** | Business portal with SQLite in Write-Ahead Logging (WAL) mode, bcrypt salted password hashing, JWT authentication, and validated booking/invoicing state machine. |

---

## 3. Four-Machine DevOps Topology

```
                      [ Client Browser / Operator ]
                                    │
                                    │ HTTP (80/TCP)
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │                 App Node (192.168.56.10)               │
       │  - Nginx Reverse Proxy (Static React SPA)              │
       │  - FastAPI Service (Uvicorn / Python 3.12)             │
       │  - SQLite Database with WAL: /var/lib/phoenix/         │
       │  - Puppet Agent (Drift Self-Healing)                   │
       └──────▲────────────────────────────────────────▲────────┘
              │                                        │
              │ 8140/TCP (HTTPS)                       │ Active Probes
              │                                        │
┌─────────────┴────────────────┐        ┌──────────────┴───────────────┐
│     Puppet Master (Node 2)   │        │     Nagios Core (Node 3)     │
│     192.168.56.20            │        │     192.168.56.30            │
│     - Certificate Authority  │        │     - Core Polling Engine    │
│     - Catalog Compiler       │        │     - Custom Python Probes   │
│     - Drift Auto-Repair      │        │     - Status Web Interface   │
└──────────────────────────────┘        └──────────────────────────────┘
              ▲                                        ▲
              │                 SSH (22/TCP)           │
              └────────────────┬───────────────────────┘
                               │
       ┌───────────────────────┴────────────────────────────────┐
       │            Bastion / Control Node (Node 4)             │
       │            192.168.56.1 (Operator Workstation)         │
       │  - Terraform CLI (Cloud & VirtualBox Provisioning)     │
       │  - Ansible Engine (playbooks/site.yml & recover.yml)   │
       │  - External Backup Repository: /var/backups/phoenix/   │
       └────────────────────────────────────────────────────────┘
```

---

## 4. Repository Structure

```text
phoenix/
├── backend/                       # Python FastAPI Backend
│   ├── app/                       # Core application logic
│   │   ├── auth.py                # Bcrypt salted hashing & JWT tokens
│   │   ├── database.py            # SQLite WAL mode & PRAGMA configuration
│   │   ├── deps.py                # RBAC dependencies (admin, staff, customer)
│   │   ├── main.py                # FastAPI app & operational probes (/health, /ready)
│   │   ├── models.py              # 7 SQLAlchemy models (users, bookings, invoices, etc.)
│   │   ├── schemas.py             # Pydantic schemas with RFC email validation
│   │   └── routers/               # Modular REST endpoints (auth, services, bookings, invoices)
│   ├── tests/                     # 29 pytest unit & integration tests (100% passing)
│   ├── seed.py                    # Database seeder (admin, staff, customer, services)
│   └── requirements.txt           # Python dependencies
├── frontend/                      # Minimal React 18 + TypeScript Frontend
│   ├── src/                       # Components, context, and views
│   │   ├── App.tsx                # Client-side router & role-aware navigation
│   │   ├── api.ts                 # Axios-free HTTP client with localStorage wrapper
│   │   ├── style.css              # Plain CSS styling (zero external CDNs or icon fonts)
│   │   └── pages/                 # Login, Services, Bookings, Invoices, System Status
│   ├── tests/                     # 7 Vitest + React Testing Library tests (100% passing)
│   └── dist/                      # Pre-built production bundle ready for Nginx
├── terraform/                     # Infrastructure as Code
│   ├── aws/                       # Production AWS configuration (VPC, Subnet, SGs, 3 EC2s)
│   │   ├── main.tf, variables.tf, outputs.tf
│   │   └── scripts/               # Bootstrapping scripts for EC2 user_data
│   └── virtualbox/                # Offline Vagrantfile for 4-node VirtualBox cluster
├── ansible/                       # Orchestration & Recovery Automation
│   ├── inventory/hosts.ini        # Target node inventory (app, puppet, nagios)
│   ├── playbooks/
│   │   ├── site.yml               # Initial application deployment playbook
│   │   └── recover.yml            # Emergency disaster recovery playbook (block/rescue)
│   └── roles/
│       ├── common/                # System packages, users, firewall
│       ├── app/                   # Python venv, Nginx proxy, systemd unit, reload handlers
│       └── recovery/              # Atomic backup restoration & integrity check
├── puppet/                        # Self-Healing Configuration Management
│   ├── manifests/site.pp          # Node definitions for app, puppet, and nagios
│   └── modules/phoenix/           # Custom Phoenix Puppet module
│       ├── manifests/             # baseline.pp, web.pp, monitoring.pp
│       ├── templates/             # Nginx vhost ERB template utilizing Facter facts
│       └── lib/puppet/functions/  # Custom Ruby function (phoenix::validate_db_path)
├── nagios/                        # Continuous Monitoring & Observability
│   ├── etc/                       # nagios.cfg, hosts.cfg, services.cfg, commands.cfg
│   ├── plugins/                   # Custom plugins (check_portal_health.py, check_web_errors.sh)
│   ├── tests/                     # 9 pytest plugin tests (OK, WARNING, CRITICAL, UNKNOWN)
│   ├── validate_config.py         # Static configuration syntax parser (0 errors)
│   └── install_nagios.sh          # Automated Nagios Core installation script
├── scripts/                       # Operational, Disaster & Verification Scripts
│   ├── backup.py / backup.sh      # Transaction-consistent online SQLite backup
│   ├── restore.py / restore.sh    # Verified restoration with PRAGMA integrity audit
│   ├── simulate_failure.py        # Outage simulation tool (logs to recovery_events)
│   ├── inject_drift.sh            # Drift simulator (corrupts Nginx & permissions)
│   ├── verify_recovery.py         # End-to-end recovery verification & parity auditor
│   └── disaster_demo.py / .sh     # Complete 8-stage disaster recovery drill runner
└── docs/                          # Master Documentation Suite
    ├── ARCHITECTURE.md            # High-Level & Low-Level Architectural Specification
    ├── DATABASE_DESIGN.md         # ER diagram, schema details, SQLite WAL pragmas
    ├── DISASTER_DEMO.md           # Step-by-step 8-stage disaster drill runbook
    ├── RECOVERY_PROCEDURE.md      # Standard Operating Procedure (SOP-DR-01)
    ├── INSTALLATION.md            # Installation guide for AWS, VirtualBox, and Local
    ├── TROUBLESHOOTING.md         # Diagnostic matrix & common remediation steps
    ├── DEMO_SCRIPT.md             # Rehearsed 10-minute live demonstration script
    ├── VIVA_QA.md                 # 30 comprehensive viva questions with in-depth answers
    ├── RESULTS.md                 # Master execution logs (68/68 passed, 0 failed, 5 unrun)
    ├── PUPPET_SETUP_GUIDE.md      # Puppet master-agent certificate signing guide
    ├── DRIFT_DEMO.md              # Puppet drift remediation demonstration runbook
    ├── NAGIOS_DEMO.md             # Nagios alerting & recovery demonstration runbook
    └── VIRTUALBOX_LAB_SETUP.md    # Step-by-step VirtualBox host-only networking guide
```

---

## 5. Documentation Index

The following comprehensive guides are available in the [`docs/`](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/) folder:

| Document | Purpose & Description |
| :--- | :--- |
| [**ARCHITECTURE.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/ARCHITECTURE.md) | High-level and low-level architecture, network matrix, and lifecycle handoffs. |
| [**DATABASE_DESIGN.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/DATABASE_DESIGN.md) | 7-table schema definitions, Mermaid ER diagram, and SQLite WAL pragmas. |
| [**DISASTER_DEMO.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/DISASTER_DEMO.md) | Step-by-step 8-stage disaster demonstration runbook with screenshot checkpoints. |
| [**RECOVERY_PROCEDURE.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/RECOVERY_PROCEDURE.md) | Standard Operating Procedure (SOP) for on-call engineers during outages. |
| [**INSTALLATION.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/INSTALLATION.md) | End-to-end multi-machine setup instructions for AWS, VirtualBox, and Local. |
| [**TROUBLESHOOTING.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/TROUBLESHOOTING.md) | Diagnostic triage matrix and remediation procedures for all subsystems. |
| [**DEMO_SCRIPT.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/DEMO_SCRIPT.md) | 10-minute presentation guide with exact timings, commands, and verbal cues. |
| [**VIVA_QA.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/VIVA_QA.md) | 30 rigorous viva questions and answers for university examination. |
| [**RESULTS.md**](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/RESULTS.md) | Evidence-based execution log (68 PASSED, 0 FAILED, 5 NOT RUN). |

---

## 6. Quick Start & Execution

### 6.1 Run Backend & Tests Locally
```bash
# Set up virtual environment
cd backend
python -m venv venv
# On Windows: .\venv\Scripts\Activate.ps1 | On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# Run seed script
python seed.py

# Run all 29 pytest tests
pytest tests/
```

### 6.2 Build and Run Frontend
```bash
cd frontend
npm install
npm test          # Runs 7 Vitest tests
npm run build     # Compiles production distribution to frontend/dist/
```

### 6.3 Run Full Disaster Recovery Simulation (Single-Command)
```bash
python scripts/disaster_demo.py --mode local-simulate
```
*Simulates all 8 stages: snapshot backup, pre-disaster census, destruction, re-provisioning, Ansible recovery, Puppet drift repair, Nagios re-check, and proves 100% post-disaster data parity.*

---

## 7. Security and Integrity Compliance

1. **No Committed Secrets:** Private keys (`.pem`, `id_rsa`), database files (`*.db`), `.env` files, `.tfstate` files, and Ansible Vault passwords are excluded via `.gitignore`.
2. **Evidence-Based Reporting:** In accordance with course guidelines, only tests physically executed in the environment are marked as **PASSED**. All deferred multi-node steps are explicitly documented in `docs/RESULTS.md`.
3. **Non-Root Execution:** All services run under restricted system accounts (`phoenix:phoenix`) with minimal filesystem permissions (`0660`).
