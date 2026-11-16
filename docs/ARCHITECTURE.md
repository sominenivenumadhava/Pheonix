# Project Phoenix: System Architecture Specification

**Project Title:** Disaster Recovery as Code for a Small Business with Self-Healing DevOps Automation  
**Course Code:** INT333 (DevOps Advanced Configuration Management)  
**Author:** Student ID 12405600  

---

## 1. Executive Summary & Design Philosophy

Small and medium-sized enterprises (SMEs) face existential risks from infrastructure failures, accidental data corruption, and cloud provider outages. However, enterprise multi-region active-active cloud clusters (Kubernetes multi-region, distributed Aurora/CockroachDB) carry prohibitive operational expenses and cognitive complexity.

**Project Phoenix** demonstrates an alternative: **Disaster Recovery as Code (DRaC)** combined with **Self-Healing Configuration Management**. By encoding the entire technology lifecycle into version-controlled automation—from raw infrastructure creation to application deployment, continuous drift repair, proactive monitoring, and atomic data restoration—a small business achieves enterprise-grade resilience:
- **RTO (Recovery Time Objective):** < 10 minutes from total infrastructure wipe to full service availability.
- **RPO (Recovery Point Objective):** Near-zero data loss through externalized, transactional SQLite snapshots.
- **Self-Healing:** Automatic detection and remediation of manual tampering and configuration drift.

---

## 2. High-Level Architecture (HLA)

The system operates across three tiers:
1. **Presentation & Application Tier:** Minimalist React + TypeScript frontend served via Nginx, proxying requests to an asynchronous Python FastAPI backend running under Uvicorn with SQLite in Write-Ahead Logging (WAL) mode.
2. **Infrastructure & Orchestration Tier:** Infrastructure as Code (Terraform) provisioning compute and networking, with Ansible managing application deployment and emergency recovery playbooks.
3. **Observability & Governance Tier:** Puppet Master continuously enforcing desired-state configurations and self-healing drift; Nagios Core continuously executing active probes and generating alerts.

```
                     ┌──────────────────────────────────────────────┐
                     │            User / Client Browser            │
                     └──────────────────────┬───────────────────────┘
                                            │ HTTP (80/TCP)
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │          App Node (192.168.56.10)            │
                     │  ┌────────────────────────────────────────┐  │
                     │  │        Nginx Reverse Proxy             │  │
                     │  │   - Serves React SPA (Static HTML/JS)  │  │
                     │  │   - Proxies /api, /auth, /health       │  │
                     │  └───────────────────┬────────────────────┘  │
                     │                      │ 127.0.0.1:8000        │
                     │  ┌───────────────────▼────────────────────┐  │
                     │  │    FastAPI Application (Uvicorn)       │  │
                     │  │   - Pydantic Validation & RBAC Auth    │  │
                     │  │   - SQLAlchemy ORM (WAL SQLite)        │  │
                     │  └───────────────────┬────────────────────┘  │
                     │                      │ File I/O              │
                     │  ┌───────────────────▼────────────────────┐  │
                     │  │    Local SQLite: /var/lib/phoenix/     │  │
                     │  └────────────────────────────────────────┘  │
                     └──────▲──────────────────────────────▲────────┘
                            │                              │
         Config Enforcement │ (8140/TCP)     Active Probes │ (Ping, HTTP, NRPE 5666)
                            │                              │
       ┌────────────────────┴──────────┐        ┌──────────┴───────────────────┐
       │   Puppet Master (Node 2)      │        │      Nagios Core (Node 3)    │
       │   192.168.56.20               │        │      192.168.56.30           │
       │   - Certificate CA            │        │      - Active Polling Engine │
       │   - Catalog Compiler          │        │      - Custom Python Probes  │
       │   - Drift Auto-Repair         │        │      - Alerting / Status UI  │
       └───────────────────────────────┘        └──────────────────────────────┘
                            ▲                              ▲
                            │                              │
                            └──────────────┬───────────────┘
                                           │ SSH (22/TCP)
                                           │
                     ┌─────────────────────┴────────────────────────┐
                     │         Bastion / Operator Node (Node 4)     │
                     │         192.168.56.1 (Control Machine)       │
                     │         - Terraform (IaC Provisioning)       │
                     │         - Ansible (Playbook Execution)       │
                     │         - Backup Storage Repository          │
                     └──────────────────────────────────────────────┘
```

---

## 3. Four-Machine DevOps Topology

The production and simulation environments are configured with 4 distinct nodes:

| Node ID | Hostname | IP Address | OS / Specs | Roles & Installed Software |
| :--- | :--- | :--- | :--- | :--- |
| **Node 1** | `app.phoenix.local` | `192.168.56.10` | Ubuntu 22.04 LTS (2 vCPU, 2GB RAM) | Nginx, Python 3.12, Uvicorn, FastAPI, SQLite, Puppet Agent, NRPE Agent |
| **Node 2** | `puppet.phoenix.local`| `192.168.56.20` | Ubuntu 22.04 LTS (2 vCPU, 4GB RAM) | Puppetserver 7/8, Certificate Authority, Hiera configuration, `phoenix` module |
| **Node 3** | `nagios.phoenix.local`| `192.168.56.30` | Ubuntu 22.04 LTS (1 vCPU, 2GB RAM) | Nagios Core 4.5.x, Apache2, PHP, Nagios Plugins, Custom Probes (`check_portal_health.py`) |
| **Node 4** | `control.phoenix.local` | `192.168.56.1` (Host) | Windows / Linux Dev Host | Terraform CLI, Ansible Core, Git Monorepo, Backup Archive (`/var/backups/phoenix`) |

### AWS Cloud Mapping
When deployed on AWS via Terraform (`terraform/aws/`):
- **VPC:** `10.0.0.0/16` with public subnet `10.0.1.0/24`.
- **App Instance:** `t2.micro` or `t3.micro` EC2 in public subnet with Elastic IP.
- **Puppet Master:** `t3.medium` EC2 (accommodates JVM heap memory requirements).
- **Nagios Host:** `t2.micro` EC2.
- **Control Node:** Operator workstation or AWS CloudShell.

---

## 4. Port and Security Group Matrix

| Source | Destination | Port / Protocol | Service | Description |
| :--- | :--- | :--- | :--- | :--- |
| Any (`0.0.0.0/0`) | App Node | `80/TCP` | HTTP | Client web browser traffic to Nginx reverse proxy |
| Operator IP | All Nodes | `22/TCP` | SSH | Administrative access and Ansible playbook execution |
| App Node | Puppet Master | `8140/TCP` | HTTPS | Puppet agent catalog retrieval and certificate exchange |
| Nagios Host | App Node | `80/TCP`, `8000/TCP` | HTTP | Health check probes (`/health`, `/ready`) |
| Nagios Host | All Nodes | `ICMP` | Ping | Host alive monitoring |
| Nagios Host | App Node | `5666/TCP` | NRPE | Remote plugin execution (disk, system load) |
| Operator IP | Nagios Host | `80/TCP` | HTTP | Access to Nagios Core Web GUI (`/nagios`) |

---

## 5. Toolchain Interaction and Lifecycle Division

A central design requirement is avoiding architectural overlap between the 4 DevOps tools. Each tool holds an exclusive, unambiguous responsibility:

```
[Phase 1: Day 0] ────────► Terraform (Infrastructure Provisioning)
                           - Creates VPC, Subnets, Security Groups, VMs/EC2.
                           - Hands off IP addresses and SSH keys to Ansible.

[Phase 2: Day 1] ────────► Ansible (Configuration & Application Deployment)
                           - Configures OS packages, Python virtual environment.
                           - Deploys frontend build & backend application.
                           - Manages disaster recovery orchestration (recover.yml).

[Phase 3: Day 2] ────────► Puppet (State Enforcement & Drift Self-Healing)
                           - Continuous background agent (30-minute interval).
                           - Detects unauthorized manual changes to Nginx or config files.
                           - Automatically reverts drift back to compiled catalog.

[Phase 4: Day 2+] ───────► Nagios Core (Continuous Health & Observability)
                           - Proactively queries `/health` and `/ready` probes.
                           - Alerts on performance degradation or service crash.
                           - Verifies success of disaster recovery restoration.
```

### Why Both Ansible and Puppet?
- **Ansible is Procedural and Push-Based:** Ideal for linear, multi-host coordinated tasks such as rolling updates, initial provisioning, and disaster recovery where strict step sequencing is mandatory (Step A must finish before Step B starts).
- **Puppet is Declarative and Pull-Based:** Ideal for long-term state maintenance. An autonomous daemon runs periodically on the agent, pulls the compiled catalog, and reconciles drift without requiring human initiation.

---

## 6. Disaster Recovery State Machine

The recovery engine models system state transitions as follows:

```
                  ┌────────────────────────┐
                  │    NORMAL (Healthy)    │◄──────────────────────────┐
                  └───────────┬────────────┘                           │
                              │ Catastrophic Outage                    │
                              ▼                                        │
                  ┌────────────────────────┐                           │
                  │    OUTAGE (Critical)   │                           │
                  │  Nagios State: CRITICAL│                           │
                  └───────────┬────────────┘                           │
                              │ Operator triggers DR                   │
                              ▼                                        │
                  ┌────────────────────────┐                           │
                  │  PROVISIONING (IaC)    │                           │
                  │  Terraform / Vagrant   │                           │
                  └───────────┬────────────┘                           │
                              │ Infrastructure Ready                   │
                              ▼                                        │
                  ┌────────────────────────┐                           │
                  │  RECOVERY (Ansible)    │                           │
                  │  App Deploy + Restore  │                           │
                  └───────────┬────────────┘                           │
                              │ Restoration Complete                   │
                              ▼                                        │
                  ┌────────────────────────┐                           │
                  │  ENFORCING (Puppet)    │                           │
                  │  Baseline Reconciliation                           │
                  └───────────┬────────────┘                           │
                              │ Catalog Applied                        │
                              ▼                                        │
                  ┌────────────────────────┐                           │
                  │  VALIDATING (Probes)   │                           │
                  │  verify_recovery.py    │───────────────────────────┘
                  └────────────────────────┘  All Probes PASS (HTTP 200, Parity 100%)
```

---

## 7. Storage and Data Flow Architecture

### SQLite in Production: Design Rationale
For small business applications processing thousands (rather than millions) of transactions per day, SQLite configured with **Write-Ahead Logging (WAL)** provides significant operational advantages:
1. **Zero Maintenance Overhead:** No database daemon process, socket configuration, or port vulnerability.
2. **Atomic Backups:** SQLite's online backup API allows hot snapshots without locking active readers.
3. **Single-File Portability:** Disaster recovery involves copying a single verified `.db` file rather than exporting and importing SQL dump streams across network boundaries.
4. **Physical Verification:** `PRAGMA integrity_check` performs low-level B-tree page validation in milliseconds.

### Backup Strategy & Off-Site Isolation
- Backups are generated using `sqlite3.connect().backup()` to ensure transaction-consistent snapshots.
- Backup files are named `phoenix_backup_YYYYMMDD_HHMMSS.db`.
- Backups are stored in `/var/backups/phoenix/` outside the application directory and mirrored off-host via Ansible.
- Every backup calculates a SHA-256 checksum and executes `PRAGMA integrity_check` before logging to `backup_records`.
