# Phoenix Puppet Master–Agent Setup Guide

This guide details how to configure the Puppet Master–Agent architecture across the Ubuntu VirtualBox VMs (`puppet-master` and `app-server`).

---

## 1. Host Resolution Prerequisites

Ensure both VMs can resolve each other by name. On both `puppet-master` and `app-server`:

```bash
sudo nano /etc/hosts
```

Ensure the following entries are present:
```text
192.168.56.20 puppet-master puppet
192.168.56.30 app-server
192.168.56.40 nagios-server
```

---

## 2. Setting Up Puppet Master (`192.168.56.20`)

### Step 2.1: Install Puppet Repository & Server
```bash
wget https://apt.puppet.com/puppet7-release-jammy.deb
sudo dpkg -i puppet7-release-jammy.deb
sudo apt-get update -y
sudo apt-get install -y puppetserver
```

### Step 2.2: Configure Java Heap Memory
For lab VMs with 3 GB RAM, adjust heap allocation in `/etc/default/puppetserver`:
```bash
sudo sed -i 's/-Xms2g -Xmx2g/-Xms1g -Xmx1g/' /etc/default/puppetserver
```

### Step 2.3: Configure `puppet.conf` on Master
Edit `/etc/puppetlabs/puppet/puppet.conf`:
```ini
[master]
vardir = /opt/puppetlabs/server/data/puppetserver
logdir = /var/log/puppetlabs/puppetserver
rundir = /var/run/puppetlabs/puppetserver
pidfile = /var/run/puppetlabs/puppetserver/puppetserver.pid
codedir = /etc/puppetlabs/code

[main]
server = puppet-master
certname = puppet-master
dns_alt_names = puppet,puppet-master
```

### Step 2.4: Start Puppetserver Daemon
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now puppetserver
sudo systemctl status puppetserver
```

---

## 3. Setting Up Puppet Agent (`app-server` at `192.168.56.30`)

### Step 3.1: Install Puppet Agent
```bash
wget https://apt.puppet.com/puppet7-release-jammy.deb
sudo dpkg -i puppet7-release-jammy.deb
sudo apt-get update -y
sudo apt-get install -y puppet-agent
```

### Step 3.2: Configure `puppet.conf` on Agent
Edit `/etc/puppetlabs/puppet/puppet.conf`:
```ini
[main]
server = puppet-master
certname = app-server
runinterval = 15m
```

---

## 4. SSL Certificate Exchange & Signing

### Step 4.1: Request Certificate from Agent
On `app-server`:
```bash
sudo /opt/puppetlabs/bin/puppet ssl bootstrap
```
*(The command submits an SSL certificate signing request (CSR) to the master and waits).*

### Step 4.2: List and Sign Certificate on Master
On `puppet-master`:
```bash
# View pending certificate requests
sudo /opt/puppetlabs/bin/puppetserver ca list

# Sign the app-server certificate
sudo /opt/puppetlabs/bin/puppetserver ca sign --certname app-server
```

### Step 4.3: Complete Handshake on Agent
On `app-server`:
The `puppet ssl bootstrap` command will complete:
```text
Notice: Completed SSL initialization
```

---

## 5. Deploying the Phoenix Module & Site Manifest

On `puppet-master`, copy the repository's Puppet manifests into the production environment:

```bash
# 1. Deploy site.pp
sudo cp /home/ubuntu/phoenix/puppet/manifests/site.pp \
  /etc/puppetlabs/code/environments/production/manifests/site.pp

# 2. Deploy phoenix module
sudo cp -r /home/ubuntu/phoenix/puppet/modules/phoenix \
  /etc/puppetlabs/code/environments/production/modules/
```

Verify permissions:
```bash
sudo chown -R root:root /etc/puppetlabs/code/environments/production/
```

---

## 6. Testing Catalog Enforcement

On `app-server`, trigger an on-demand catalog compilation:
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
Info: Applying configuration version '...'
Notice: /Stage[main]/Phoenix::Baseline/Package[htop]/ensure: created
Notice: /Stage[main]/Phoenix::Baseline/User[phoenix]/ensure: created
Notice: /Stage[main]/Phoenix::Baseline/File[/etc/phoenix-baseline.conf]/ensure: defined content as '...'
Notice: /Stage[main]/Phoenix::Web/Package[nginx]/ensure: created
Notice: /Stage[main]/Phoenix::Web/File[/etc/nginx/sites-available/phoenix]/ensure: defined content as '...'
Notice: /Stage[main]/Phoenix::Web/Service[nginx]/ensure: ensure changed 'stopped' to 'running'
Notice: Applied catalog in 8.35 seconds
```
Re-running `sudo puppet agent -t` will output `0 changes` (idempotence confirmed).
