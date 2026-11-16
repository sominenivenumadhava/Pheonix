# Project Phoenix: 30 Comprehensive Viva Examination Questions & In-Depth Answers

**Course:** INT333 (DevOps Advanced Configuration Management)  
**Topic:** Disaster Recovery as Code, Self-Healing Automation, and Infrastructure Management  

---

### Category 1: DevOps Toolchain Roles & Comparisons

#### Q1: What is the distinct responsibility of each tool in the Phoenix architecture? Why not use just Ansible for everything?
**Answer:**
Each tool fulfills a specialized role in the system lifecycle:
1. **Terraform (Day 0 - Infrastructure Provisioning):** Declaratively creates cloud resources (VPCs, Subnets, Security Groups, Virtual Machines) via APIs. Terraform excels at lifecycle management of raw cloud infrastructure.
2. **Ansible (Day 1 & Recovery - Procedural Orchestration):** Push-based, agentless orchestration tool executing linear playbooks. It is ideally suited for initial application bootstrapping and emergency disaster recovery where strict execution sequencing is mandatory.
3. **Puppet (Day 2+ - Continuous State Enforcement & Drift Remediation):** Declarative, pull-based agent continuously polling every 30 minutes to compare actual system state against the compiled catalog and automatically reversing unauthorized drift.
4. **Nagios Core (Observability):** Active polling engine evaluating system health, triggering alerts, and confirming recovery.

*Why not just Ansible?* Ansible is push-based and requires an external trigger or cron job on a control node to run. If an administrator alters a config file locally on a server, Ansible will not know or repair it until pushed. Puppet's native agent runs locally in the background, continuously maintaining compliance without operator intervention.

---

#### Q2: Contrast Declarative vs. Procedural Configuration Management. How do Terraform, Ansible, and Puppet classify?
**Answer:**
- **Declarative Approach:** You describe *what* the desired end-state should be, and the tool calculates the difference between current state and desired state to apply necessary actions.
  - *Terraform* is declarative (`resource "aws_instance"` specifies the desired instance count and shape).
  - *Puppet* is declarative (`file { '/etc/nginx/nginx.conf': ensure => file }` defines what should exist).
- **Procedural (Imperative) Approach:** You describe *how* to achieve a state through a sequence of steps.
  - *Ansible* is primarily procedural in structure (playbooks execute task-by-task from top to bottom), though individual Ansible modules within tasks are written to be declarative and idempotent.

---

#### Q3: Contrast Push-based vs. Pull-based configuration architectures. What are the trade-offs?
**Answer:**
- **Push-based (e.g., Ansible):** The control node initiates an SSH connection to target nodes, executes commands/modules, and disconnects.
  - *Pros:* Agentless, zero footprint on managed nodes, immediate on-demand execution.
  - *Cons:* Control node needs network route and SSH keys to every node; scaling to 10,000 nodes introduces control node CPU/socket bottlenecks.
- **Pull-based (e.g., Puppet Master-Agent):** Each managed node runs an autonomous background daemon (`puppet-agent`) that periodically queries the Puppet Master over HTTPS (port 8140), downloads its compiled catalog, and enforces it locally.
  - *Pros:* Self-healing, resilient to transient network disconnections, scales efficiently.
  - *Cons:* Requires agent installation and memory overhead on managed nodes; certificate management overhead.

---

#### Q4: What is the difference between Disaster Recovery (DR), High Availability (HA), and simple Data Backups?
**Answer:**
- **Backups:** Copies of data stored elsewhere. Having a backup does not mean you have a functioning system—you still need a documented or automated mechanism to provision infrastructure and restore data.
- **High Availability (HA):** Multi-node redundancy (e.g., active-passive or active-active clusters with load balancers) designed to eliminate single points of failure so users experience zero downtime during individual component failures. HA is expensive and does not protect against data corruption replicated across nodes.
- **Disaster Recovery (DR):** The documented and automated process to rebuild and restore entire systems to operational status following a catastrophic event (datacenter destruction, ransomware, hypervisor loss). Phoenix implements **Disaster Recovery as Code**.

---

### Category 2: Idempotence & Configuration Drift

#### Q5: What is "Idempotence" in DevOps? How is it mathematically and practically defined?
**Answer:**
Idempotence is the property of an operation whereby applying it multiple times produces the exact same result as applying it once, with no unintended side effects.  
Mathematically: `f(f(x)) = f(x)`.  
In Phoenix:
- In **Ansible:** Running `ansible-playbook site.yml` the first time results in `changed=9`. Running it a second time immediately results in `changed=0` because all files, users, and packages already exist in the desired state.
- In **Puppet:** Applying a manifest on an already compliant node reports `Applied catalog in 0.2s` with 0 resource changes.

---

#### Q6: How did you prove idempotence in your project?
**Answer:**
We verified idempotence through two consecutive runs:
1. In Ansible: We run the playbook once (all tasks return `ok` or `changed`), then immediately re-run the exact same playbook. On the second run, all tasks report `ok`, with `changed=0` and `failed=0`.
2. In Puppet: We execute `sudo puppet agent -t` once to apply changes. A subsequent execution produces zero change notices and returns exit code 0.

---

#### Q7: What is "Configuration Drift"? Give a concrete scenario and explain how Phoenix self-heals it.
**Answer:**
Configuration drift occurs when the runtime configuration of a system deviates from its intended, source-controlled specification due to manual ad-hoc changes, emergency hotfixes, package updates, or unauthorized tampering.  
*Scenario in Phoenix:* An administrator logs into the App Node and mistakenly modifies `/etc/nginx/sites-available/phoenix` to proxy port 9999 instead of 8000, corrupts the database permissions to 0777, and stops Nginx.  
*Remediation:* When the Puppet agent executes (either on its 30-minute schedule or via `puppet agent -t`), it compares the local files against its compiled catalog from the Puppet Master. Puppet detects the hash mismatch, overwrites the file back to the ERB template specification, resets file permissions to `0660`, and issues `systemctl start nginx`.

---

### Category 3: Disaster Recovery Metrics & Database Design

#### Q8: What are RTO and RPO? What are the measured RTO and RPO for Project Phoenix?
**Answer:**
- **RTO (Recovery Time Objective):** The maximum acceptable elapsed time between disaster declaration and full system restoration.
  - *Phoenix Measured RTO:* **< 7 minutes** (Terraform infrastructure provisioning: ~2.5 mins; Ansible application deployment & database restoration: ~3.5 mins; validation: ~30 secs).
- **RPO (Recovery Point Objective):** The maximum acceptable age of data lost due to a disaster event.
  - *Phoenix Measured RPO:* Dependent on snapshot schedule (e.g., hourly = 1 hour max; using automated cron snapshots before maintenance = **0 data loss**). In our disaster drill, we mathematically proved 100% data parity with 0 records lost.

---

#### Q9: Why did you choose SQLite instead of PostgreSQL or MySQL for a small business?
**Answer:**
1. **Operational Simplicity:** SQLite requires zero server daemons, no background memory footprints, no network port exposure (reducing attack surface), and zero connection pool tuning.
2. **Atomic Hot Backups:** SQLite's native C Backup API (`sqlite3_backup`) permits non-blocking online snapshots while reader transactions are actively occurring.
3. **Single-File Disaster Recovery:** The entire database resides in a single portable file (`phoenix.db`). Restoring during a disaster requires copying one file and running integrity checks, avoiding complex SQL dump/restore pipe errors or database version incompatibilities.
4. **Performance:** For a small business with under 100,000 transactions/day, SQLite embedded directly in process memory easily handles thousands of queries per second with sub-millisecond latencies.

---

#### Q10: What is SQLite WAL mode and why is it critical for Phoenix?
**Answer:**
WAL stands for **Write-Ahead Logging**. In traditional rollback journal mode, writing to SQLite locks the entire database file, preventing any reads.  
In WAL mode:
1. Changes are written to a separate `.db-wal` file.
2. Readers read from the original database pages and the WAL file concurrently without locking writers.
3. Writers do not block readers, enabling high read concurrency in our FastAPI application.
4. Periodic checkpoints merge the WAL changes back into the main `.db` file.

---

#### Q11: What are the architectural limits of SQLite, and when must a business migrate to PostgreSQL?
**Answer:**
SQLite has two primary architectural limitations:
1. **Single Writer Concurrency:** While many threads can read concurrently in WAL mode, only one process/thread can write at any single instant. Under very high write transaction volumes (>50–100 writes/second continuously), requests experience `SQLITE_BUSY` timeouts.
2. **Distributed Architecture:** SQLite cannot span across multiple server nodes.

*Migration Triggers:* A business must migrate to PostgreSQL when:
- Continuous write throughput exceeds 100 writes/second.
- Database size exceeds 500 GB.
- Multi-region active-active read/write replicas are mandated.
- Strict row-level or column-level access controls are required.

---

### Category 4: Infrastructure as Code (Terraform)

#### Q12: What is the purpose of the `terraform.tfstate` file, and why should it never be committed to Git?
**Answer:**
The `terraform.tfstate` file is Terraform's single source of truth mapping your declarative HCL configuration to real-world cloud resources (IDs, metadata, IPs).  
*Why never commit to Git?*
1. **Security:** State files often contain plaintext sensitive values (passwords, private keys, database connection strings).
2. **Concurrency / State Corruption:** If multiple developers commit conflicting state files, the infrastructure becomes corrupted.
3. **Best Practice:** State files should be stored in a remote backend with encryption and distributed state locking (e.g., AWS S3 + DynamoDB).

---

#### Q13: What is the difference between `terraform plan` and `terraform apply`?
**Answer:**
- `terraform plan`: An execution planning command that queries the cloud provider API to refresh state, compares it with the local `.tf` files, and generates a speculative delta detailing exactly what resources will be created (`+`), modified (`~`), or destroyed (`-`) without making any actual changes.
- `terraform apply`: Executes the changes specified in the execution plan to bring the real-world infrastructure into alignment with the configuration.

---

#### Q14: How are Terraform workspaces used in Project Phoenix?
**Answer:**
Terraform workspaces (`dev` and `prod`) allow managing multiple distinct environments from a single unified codebase. By reading `terraform.workspace`, the configuration can dynamically vary instance sizing (e.g., `t2.micro` for dev vs `t3.small` for prod), environment tags, and subnet allocations without duplicating `.tf` code.

---

### Category 5: Configuration Management (Ansible & Puppet)

#### Q15: How does Ansible ensure security when handling sensitive data like JWT secrets or database passwords?
**Answer:**
Ansible utilizes **Ansible Vault**, which provides AES-256 encryption for variable files or specific string values (e.g., `ansible/vars/vault.yml`). Encrypted files can be safely committed to version control. The encryption password is never stored in Git; it is supplied at runtime via `--ask-vault-pass` or through an uncommitted secret file referenced by `--vault-password-file`.

---

#### Q16: What is the role of Ansible Handlers, and how do they optimize playbook execution?
**Answer:**
Handlers in Ansible are special tasks that only execute when triggered by a `notify` directive from a preceding task, and only if that preceding task resulted in a `changed` status. Furthermore, handlers execute once at the end of the play, preventing repeated service reloads.  
*Example in Phoenix:* When copying Nginx configurations, `notify: reload nginx` ensures Nginx only reloads if the configuration file was genuinely modified.

---

#### Q17: What is the purpose of the `block:` and `rescue:` construct in your `recover.yml` playbook?
**Answer:**
The `block:` and `rescue:` construct provides structured exception handling in Ansible.  
In `recover.yml`:
- The `block:` contains tasks to stop the service, copy the backup, and run `restore.py`.
- If any task inside the block fails (e.g., corrupted backup file or integrity failure), execution immediately jumps to the `rescue:` block.
- The `rescue:` block reverts to the pre-recovery database state, logs an emergency `RESTORE_FAILED` alert, and restarts the service, preventing the node from remaining in a broken state.

---

#### Q18: In Puppet, what is the role of Facter? Give an example of how Phoenix uses Facter facts.
**Answer:**
Facter is Puppet's system inventory tool. Before compiling a catalog, the Puppet agent runs Facter to collect system facts (e.g., IP addresses, OS distribution, memory, architecture) and sends them to the Master.  
*In Phoenix:* In our Nginx EPP/ERB template (`puppet/modules/phoenix/templates/nginx_vhost.erb`), we reference `@networking['ip']` and `@fqdn` to dynamically bind Nginx server names and headers to the node's real IP address.

---

#### Q19: Explain Puppet's Master-Agent certificate exchange and authentication mechanism.
**Answer:**
Puppet uses mutually authenticated SSL/TLS certificates:
1. The agent generates a private key and sends a Certificate Signing Request (CSR) to the Puppet Master over port 8140.
2. The Puppet Master (acting as the Certificate Authority) signs the CSR (`puppetserver ca sign --certname <agent>`).
3. The signed client certificate is downloaded by the agent.
4. Future catalog communications use mutual TLS, guaranteeing that only authorized nodes receive sensitive catalogs.

---

### Category 6: Continuous Monitoring (Nagios Core)

#### Q20: What is the Nagios plugin API contract for exit codes?
**Answer:**
Nagios requires plugins to return standardized integer exit codes that dictate service status:
- **`0 (OK)`:** The service is operating normally within acceptable performance thresholds.
- **`1 (WARNING)`:** The service is functional but approaching a warning threshold (e.g., high latency, elevated error rate).
- **`2 (CRITICAL)`:** The service is down, unreachable, or exceeding critical error thresholds.
- **`3 (UNKNOWN)`:** The plugin encountered an internal error, missing arguments, or invalid syntax and cannot determine status.

---

#### Q21: Explain the format and importance of Nagios Performance Data (perfdata).
**Answer:**
Performance data allows Nagios and graphing tools (like PNP4Nagios or Graphite) to store metrics over time.  
In our custom plugin `check_portal_health.py`:
```
PORTAL OK - Status: healthy, DB: ok | response_time=0.012s;0.500;1.500;0;5.000
```
- The pipe `|` separates human-readable text from perfdata.
- `response_time=0.012s`: Metric name and observed value.
- `;0.500`: Warning threshold.
- `;1.500`: Critical threshold.
- `;0`: Minimum boundary.
- `;5.000`: Maximum boundary.

---

#### Q22: What is the difference between active checks and passive checks in Nagios?
**Answer:**
- **Active Checks:** Initiated by the Nagios Core scheduler on a regular interval (e.g., every 60 seconds). Nagios executes a local binary or probe (like `check_ping` or `check_portal_health.py`) which reaches out to the target host and collects status.
- **Passive Checks:** Initiated by external applications or remote hosts. The remote application sends status information to Nagios's command pipe (`nagios.cmd`). Nagios simply processes the message without initiating polling. Phoenix uses **Active Checks** for reliable proactive polling.

---

### Category 7: Application Architecture & Security

#### Q23: Why do we use JWT (JSON Web Tokens) with short lifespans and bcrypt hashing?
**Answer:**
- **bcrypt Hashing:** Passwords are never stored in plaintext. `bcrypt` incorporates a random per-user salt and a configurable work factor (computational cost), making dictionary and rainbow-table attacks computationally infeasible.
- **Short-Lived JWTs:** JWTs are stateless and signed cryptographically with a secret key. A short expiration (e.g., 60 minutes) limits the window of vulnerability if a token is intercepted, forcing re-authentication without burdening the database with server-side session lookups.

---

#### Q24: How is Role-Based Access Control (RBAC) enforced in the Phoenix FastAPI backend?
**Answer:**
RBAC is enforced declaratively at the route level using FastAPI's dependency injection system:
```python
@router.post("/services", dependencies=[Depends(require_role("admin"))])
def create_service(...):
```
The `require_role` dependency decodes the JWT, validates that `is_active` is True, checks the user's role against permitted roles, and automatically raises HTTP 403 Forbidden if unauthorized.

---

#### Q25: How does the booking state machine prevent illegal invoice generation?
**Answer:**
In `backend/app/routers/invoices.py`, the invoice creation logic explicitly validates the booking state:
```python
if booking.status != "completed":
    raise HTTPException(status_code=400, detail="Invoices can only be generated for completed bookings.")
```
Invoices cannot be created for `pending`, `confirmed`, or `cancelled` bookings. Furthermore, a unique constraint on `invoices.booking_id` prevents duplicate billing.

---

### Category 8: Disaster Recovery & Verification

#### Q26: How does `scripts/backup.py` guarantee data consistency if a transaction is occurring at the exact moment of backup?
**Answer:**
Instead of copying the raw SQLite file (which can lead to torn pages or corruption if copied mid-write), `scripts/backup.py` utilizes SQLite's online backup API (`sqlite3.Connection.backup()`). This API acquires a read lock on the database pages, copies consistent page frames while respecting WAL journal locks, and releases the lock once complete.

---

#### Q27: How does `scripts/restore.py` verify a backup before replacing the primary database?
**Answer:**
Restoration follows a strict 4-step safety pipeline:
1. **Cryptographic Validation:** Recalculates the SHA-256 hash of the backup file and verifies it matches the catalog record.
2. **Low-Level Integrity Check:** Runs `PRAGMA integrity_check` directly on the backup file to ensure zero B-tree or page corruption.
3. **Census Check:** Verifies that required core tables (`users`, `services`) exist and contain data.
4. **Atomic Deployment:** Uses `shutil.copy2` to deploy the verified file, followed by `PRAGMA foreign_key_check` on the live database.

---

#### Q28: What is the purpose of `scripts/verify_recovery.py`?
**Answer:**
`verify_recovery.py` is the automated acceptance engine for disaster recovery. It programmatically validates:
1. HTTP `/health` probe (asserts HTTP 200, `status: healthy`, `database: ok`).
2. HTTP `/ready` probe (asserts HTTP 200, `ready: true`).
3. SQLite physical file integrity (`PRAGMA integrity_check == ok`).
4. Table row census across all 7 tables.
5. Audit trail: Inserts an immutable `RECOVERY_VERIFIED` event into the `recovery_events` table.

---

#### Q29: What happens if the primary Puppet Master server itself fails in a real production environment?
**Answer:**
In a production enterprise deployment:
1. Puppet Masters are deployed in a High Availability (HA) topology with a primary CA master and multiple compile masters behind a load balancer.
2. For small businesses, the Puppet codebase is stored in version control (Git). If the Master server fails, Terraform re-provisions a new VM, and the Puppet manifests are cloned from Git in under 3 minutes.
3. Agent nodes will continue running with their existing cached catalog until the Master is restored, ensuring zero service disruption.

---

#### Q30: What was the most challenging technical hurdle during the 5-day implementation of Project Phoenix, and how did you resolve it?
**Answer:**
The most critical challenge was synchronizing state across the 4 tools without creating circular dependencies. Specifically:
- Terraform provisions the infrastructure, but does not configure applications.
- Ansible deploys the application and database, but if Puppet runs immediately afterwards without coordination, Puppet might detect the newly deployed files as unauthorized drift and overwrite them.
*Solution:* We established clear boundaries in Puppet's manifests: Puppet manages baseline system configuration, firewall rules, and the Nginx reverse proxy template, while delegating application code and SQLite database contents to Ansible and the application service user. We also implemented strict file ownership (`phoenix:phoenix` with mode `0660`), which Puppet enforces without touching database data.
