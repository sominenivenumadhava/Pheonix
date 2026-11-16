# Phoenix Puppet Configuration Management & Self-Healing Module

Declarative Puppet manifests, classes, ERB templates, and custom functions implementing baseline enforcement and automated drift remediation.

---

## 1. Module Structure

```text
puppet/
├── manifests/
│   └── site.pp                 # Node categorization (default, app-server, nagios, puppet-master)
└── modules/
    └── phoenix/
        ├── manifests/
        │   ├── init.pp         # Entry point invoking validate_db_path & classes
        │   ├── baseline.pp     # Packages, phoenix user, SSH config, /opt/phoenix permissions
        │   ├── web.pp          # Nginx package, service, and ERB template virtual host
        │   └── monitoring.pp   # NRPE daemon and Nagios remote check commands
        ├── templates/
        │   ├── nginx_vhost.conf.erb # Facter-templated virtual host config
        │   └── nrpe.cfg.erb         # NRPE configuration template
        └── lib/puppet/functions/phoenix/
            └── validate_db_path.rb  # Custom Puppet 4+ function
```

---

## 2. Syntax Validation Commands (Run on Puppet Master VM)

From `puppet-master` VM:
```bash
# Validate site manifest
sudo puppet parser validate /etc/puppetlabs/code/environments/production/manifests/site.pp

# Validate module manifests
sudo puppet parser validate /etc/puppetlabs/code/environments/production/modules/phoenix/manifests/*.pp
```

---

## 3. Testing Local Enforcement (`puppet apply`)

To test manifest application locally on `app-server` without the master daemon:
```bash
# Dry run (--noop)
sudo puppet apply --noop \
  --modulepath=/home/ubuntu/phoenix/puppet/modules \
  -e "include phoenix::baseline, phoenix::web"

# Apply for real
sudo puppet apply \
  --modulepath=/home/ubuntu/phoenix/puppet/modules \
  -e "include phoenix::baseline, phoenix::web"

# Verify idempotence (second run = 0 changes)
sudo puppet apply \
  --modulepath=/home/ubuntu/phoenix/puppet/modules \
  -e "include phoenix::baseline, phoenix::web"
```

---

## 4. Drift Injection & Self-Healing Demo

Refer to [`docs/DRIFT_DEMO.md`](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/DRIFT_DEMO.md) for the complete demonstration runbook.
