# Phoenix Ansible Automation & Disaster Recovery

Declarative Ansible roles and playbooks managing application deployment, Nginx reverse proxy configuration, and the human-triggered Disaster Recovery (DR) restoration workflow.

---

## 1. Directory Structure

```text
ansible/
├── ansible.cfg              # Default inventory, timeout, and privilege escalation
├── inventory/
│   └── hosts.ini            # Node groups: app, puppet, nagios with IP variables
├── vars/
│   ├── vault.yml.example    # Template for sensitive credentials (JWT key, passwords)
│   └── secrets.yml          # Variable mappings with safe fallback defaults
├── roles/
│   ├── common/              # System baseline: packages, phoenix user, UFW firewall
│   ├── app/                 # Virtualenv, backend code, Nginx proxy, systemd unit
│   └── recovery/            # Disaster Recovery: Block & Rescue backup restoration
└── playbooks/
    ├── site.yml             # Full infrastructure deployment playbook
    └── recover.yml          # Preflight -> Rebuild -> Restore DB -> Health check
```

---

## 2. Managing Secrets with Ansible Vault

Per project rules, secrets and vault passwords must **never** be committed to source control.

### Step 1: Create Your Local Vault File
```bash
cp vars/vault.yml.example vars/vault.yml
```

### Step 2: Encrypt with Ansible Vault
```bash
ansible-vault encrypt vars/vault.yml
```
Enter a secure password when prompted.

### Step 3: Running Playbooks with Vault
Pass `--ask-vault-pass` when running playbooks:
```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --ask-vault-pass
```

---

## 3. Playbook Syntax Verification

From the Linux control node (or VirtualBox control VM):
```bash
# Verify site.yml syntax
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --syntax-check

# Verify recover.yml syntax
ansible-playbook -i inventory/hosts.ini playbooks/recover.yml --syntax-check
```

---

## 4. Execution & Disaster Recovery

### Full Deployment (`site.yml`)
Deploys baseline system configurations to all nodes and provisions the application on `app-server`:
```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

### Proving Idempotence
Run the playbook twice. On the second run, all tasks should report `ok` with `changed=0`:
```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

### Executing Disaster Recovery (`recover.yml`)
When a server failure is detected by Nagios:
1. Re-provision the infrastructure via Terraform (`terraform apply`).
2. Run the recovery playbook:
```bash
ansible-playbook -i inventory/hosts.ini playbooks/recover.yml
```
This triggers:
- Preflight network and SSH checks
- Application environment deployment
- Atomic restoration of the latest verified backup via `scripts/restore.py`
- Service start and automated `/health` and `/ready` verification
