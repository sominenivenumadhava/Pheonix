# Phoenix – Disaster Recovery as Code for a Small Business with Self-Healing DevOps Automation

> **Course**: INT333 – DevOps Advance Configuration Management  
> **Student**: Somineni Venumadhava (Reg. No: 12405600)  
> **Institution**: Lovely Professional University  

---

## 1. Project Overview

**Phoenix** is an end-to-end Disaster Recovery as Code (DRaC) and Self-Healing DevOps solution designed for small business operational continuity. Small businesses typically run bookings, billing, and customer records on a single, manually configured server without reproducible backups or monitoring. When that server fails, business stops.

Phoenix eliminates this vulnerability by declaring the complete system as code:
1. **Terraform**: Declares and provisions reproducible infrastructure across AWS EC2 (VPC, Security Groups, EC2) and an offline VirtualBox equivalent.
2. **Puppet (Master-Agent)**: Enforces the baseline configuration of every server (packages, users, SSH, Nginx virtual hosts) and automatically repairs configuration drift without manual intervention.
3. **Ansible**: Orchestrates application deployment, configuration management, and executes a human-triggered disaster-recovery playbook with automated database restoration.
4. **Nagios Core**: Continuously monitors host and service health using custom plugins (`check_portal_health` in Python, `check_web_errors` in Bash), proving recovery rather than assuming it.
5. **Business Application**: A lightweight, resilient small business portal with a **FastAPI + SQLite** backend and a **React + TypeScript + Vite** frontend (plain CSS, zero external CDN/icon dependencies).

---

## 2. Monorepo Structure

```text
phoenix/
├── backend/            # Python / FastAPI / SQLAlchemy / SQLite / Alembic
│   ├── app/            # API routers, business services, models, schemas
│   ├── tests/          # pytest unit and integration test suite
│   ├── requirements.txt# Backend dependencies
│   └── alembic/        # Database schema migrations
├── frontend/           # React 18+ / TypeScript / Vite / Plain CSS
│   ├── src/            # Components, views, auth context, API client
│   ├── tests/          # Vitest and React Testing Library tests
│   └── package.json    # Frontend dependencies and scripts
├── terraform/          # Infrastructure as Code (IaC)
│   ├── aws/            # AWS VPC, Security Groups, EC2 instances (dev & prod workspaces)
│   └── virtualbox/     # VirtualBox provider definitions for offline demonstration
├── ansible/            # Deployment & Recovery Automation
│   ├── inventory/      # Host inventory mappings (AWS and VirtualBox)
│   ├── playbooks/      # Site deployment and disaster recovery playbooks
│   ├── roles/          # Modular roles (common, app_deploy, backup_restore, nginx)
│   └── vars/           # Vault-protected configuration variables
├── puppet/             # Configuration Management & Drift Healing
│   ├── manifests/      # Master node definitions (site.pp)
│   └── modules/phoenix/# Custom Phoenix module (baseline, web, monitoring, custom functions)
├── nagios/             # Observability & Continuous Monitoring
│   ├── etc/            # Nagios Core host, service, and command definitions
│   └── plugins/        # Custom monitoring plugins (check_portal_health.py, check_web_errors.sh)
├── scripts/            # Operational & Disaster Simulation Scripts
│   ├── backup_db.sh    # Automated SQLite snapshotting and integrity check
│   ├── restore_db.sh   # Validated database restoration script
│   ├── inject_drift.sh # Deliberate drift simulator (proves Puppet self-healing)
│   └── disaster_sim.sh # Complete destroy-and-rebuild simulation runner
└── docs/               # Architecture, Specifications & Verification Logs
    ├── ARCHITECTURE.md # Comprehensive High-Level and Low-Level architecture
    ├── DATABASE_DESIGN.md # SQLite schema, ER diagram, and backup specifications
    ├── RESULTS.md      # Test and verification execution records (no invented results)
    └── RUNBOOK.md      # Step-by-step manual execution and viva guide
```

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React, TypeScript, Vite, Plain CSS | Responsive staff & customer portal; zero external CDNs |
| **Backend** | Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, Uvicorn | High-performance asynchronous REST API and health probes |
| **Database** | SQLite 3.35+ (WAL mode, Foreign Keys ON) | Zero-overhead relational data store with external verified backups |
| **Infrastructure** | Terraform 1.5+ | AWS EC2 / VPC provisioning with VirtualBox offline parity |
| **Configuration** | Puppet 7/8 (Master-Agent) | Idempotent baseline enforcement and drift self-healing |
| **Orchestration** | Ansible Core 2.15+ | Application deployment, secret vaults, and disaster recovery |
| **Observability** | Nagios Core 4.x | Real-time service monitoring with custom Python and Bash plugins |
| **Testing** | pytest, Vitest, React Testing Library | Full-stack automated verification |

---

## 4. Disaster Recovery Workflow (Summary)

```text
[ NORMAL ] ──(Tampered config / stopped service)──> [ DRIFT DETECTED ]
    │                                                        │
    │                                            (Puppet auto-heals baseline)
    │                                                        v
    │                                                   [ NORMAL ]
    │
(Server crash / Disk failure)
    v
[ FAILURE DETECTED ] (Nagios alarms CRITICAL)
    │
    v (Operator triggers recovery)
[ REBUILDING ] (Terraform apply recreates network & compute)
    │
    v (Ansible deploys code & restores latest verified DB backup)
[ DEPLOYING ]
    │
    v (Puppet agent applies and locks configuration baseline)
[ ENFORCING ]
    │
    v (Nagios re-checks all hosts, endpoints, and logs)
[ VERIFYING ]
    │
    v (All checks green: OK)
[ RECOVERED ] ──> Business operations resumed & audit log recorded
```

---

## 5. Security & Development Rules

1. **No Committed Secrets**: Cloud credentials, Ansible Vault passwords, and database files are strictly ignored via `.gitignore`.
2. **Evidence-Based Results**: No test result is claimed as passing unless physically executed. All verified results and unrun items are logged in [`docs/RESULTS.md`](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/RESULTS.md).
3. **Strict Idempotency**: All Puppet manifests and Ansible playbooks are safe to execute repeatedly without unintended state alterations.
4. **Explicit Manual Commands**: Every task lists required elevated (`sudo`), cloud, or hypervisor commands with expected outputs.
