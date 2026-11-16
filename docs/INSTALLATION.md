# Project Phoenix: Comprehensive Installation & Setup Guide

**Applies to:** AWS Cloud, VirtualBox 4-VM Offline Lab, and Local Development Mode  
**Course:** INT333 (DevOps Advanced Configuration Management)  

---

## 1. Prerequisites and System Requirements

### Host Machine Hardware Requirements
- **CPU:** Dual-core 64-bit x86_64 processor (Quad-core recommended for VirtualBox lab).
- **RAM:** Minimum 8 GB RAM (16 GB recommended to run 3–4 VMs simultaneously).
- **Disk:** At least 25 GB free disk space.
- **Operating System:** Ubuntu 22.04 LTS, Debian 12, macOS, or Windows 10/11 with PowerShell / WSL2.

### Host Software Prerequisites
| Tool | Minimum Version | Installation Command (Ubuntu / Debian) |
| :--- | :--- | :--- |
| **Python** | 3.10+ (3.12 tested) | `sudo apt install -y python3 python3-venv python3-pip` |
| **Node.js & npm** | Node 18+ (20+ LTS) | `curl -fsSL https://deb.nodesource.com/setup_20.x \| sudo -E bash - && sudo apt install -y nodejs` |
| **Git** | 2.34+ | `sudo apt install -y git` |
| **Terraform** | 1.5+ | `wget -O- https://apt.releases.hashicorp.com/gpg \| sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \| sudo tee /etc/apt/sources.list.d/hashicorp.list && sudo apt update && sudo apt install terraform` |
| **Vagrant & VirtualBox** | Vagrant 2.3+, VBox 7.0+ | `sudo apt install -y virtualbox vagrant` |
| **Ansible** | Core 2.14+ | `pip3 install --user ansible` |

---

## 2. Deployment Option A: VirtualBox Offline Lab (Recommended for Exam Demos)

This option provisions a self-contained 4-node network entirely on your laptop with no cloud costs or external internet requirements after initial download.

### Step 1: Network Topology Setup
The lab uses two network adapters on each VM:
- **Adapter 1 (NAT):** For external package installations.
- **Adapter 2 (Host-Only):** Fixed private subnet `192.168.56.0/24` for internal communication.

Ensure the VirtualBox Host-Only network `vboxnet0` is created:
```bash
# On Linux / macOS:
vboxmanage hostonlyif create
vboxmanage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0
```

### Step 2: Spin Up All 3 Managed Nodes via Vagrant
```bash
cd terraform/virtualbox
vagrant up
```
This boots:
- `app.phoenix.local` (`192.168.56.10`)
- `puppet.phoenix.local` (`192.168.56.20`)
- `nagios.phoenix.local` (`192.168.56.30`)

### Step 3: Distribute SSH Keys
From the host machine, generate an SSH key (if not already present) and trust the VMs:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_phoenix -N ""
ssh-copy-id -i ~/.ssh/id_phoenix.pub vagrant@192.168.56.10
ssh-copy-id -i ~/.ssh/id_phoenix.pub vagrant@192.168.56.20
ssh-copy-id -i ~/.ssh/id_phoenix.pub vagrant@192.168.56.30
```

---

## 3. Deployment Option B: AWS Cloud Deployment (Terraform)

For deploying onto AWS public cloud infrastructure.

### Step 1: Configure AWS CLI Credentials
Ensure you have IAM credentials with EC2, VPC, and Security Group permissions:
```bash
aws configure
# Enter AWS Access Key ID, Secret Access Key, and default region (e.g., us-east-1)
```

### Step 2: Initialize & Validate Terraform
```bash
cd terraform/aws
terraform init
terraform validate
```

### Step 3: Plan and Apply Infrastructure
```bash
terraform workspace select dev || terraform workspace new dev
terraform plan -out=tfplan.binary
terraform apply tfplan.binary
```
Terraform will output the public IP addresses of the three created instances.

---

## 4. Configuring Application & Configuration Management

### 4.1 Deploying the App Node via Ansible
On your control machine:
1. Verify SSH connectivity across inventory:
   ```bash
   cd ansible
   ansible -i inventory/hosts.ini all -m ping
   ```
2. Execute full deployment playbook:
   ```bash
   ansible-playbook -i inventory/hosts.ini playbooks/site.yml
   ```
3. Test portal availability:
   ```bash
   curl http://192.168.56.10/health
   # Expected response: {"status":"healthy","database":"ok","timestamp":"..."}
   ```

---

### 4.2 Configuring the Puppet Master & Agent
1. SSH into the Puppet Master:
   ```bash
   ssh ubuntu@192.168.56.20
   ```
2. Follow the detailed setup instructions in `docs/PUPPET_SETUP_GUIDE.md`:
   - Install `puppetserver` and configure memory: `JAVA_ARGS="-Xms1g -Xmx1g"`.
   - Start the service: `sudo systemctl start puppetserver`.
   - Copy the module: `cp -r /path/to/puppet/modules/phoenix /etc/puppetlabs/code/environments/production/modules/`.
   - Copy `puppet/manifests/site.pp` to `/etc/puppetlabs/code/environments/production/manifests/site.pp`.
3. Sign the App Node certificate on the Master:
   ```bash
   sudo /opt/puppetlabs/bin/puppetserver ca sign --certname app.phoenix.local
   ```
4. Verify Puppet enforcement on App Node:
   ```bash
   ssh ubuntu@192.168.56.10 "sudo puppet agent -t"
   ```

---

### 4.3 Configuring Nagios Core Monitoring
1. SSH into the Nagios VM:
   ```bash
   ssh ubuntu@192.168.56.30
   ```
2. Run the automated installer:
   ```bash
   chmod +x /path/to/nagios/install_nagios.sh
   sudo /path/to/nagios/install_nagios.sh
   ```
3. Deploy the custom configuration files from `nagios/etc/` to `/usr/local/nagios/etc/objects/`.
4. Deploy the custom Python plugins:
   ```bash
   sudo cp /path/to/nagios/plugins/check_portal_health.py /usr/local/nagios/libexec/
   sudo chmod +x /usr/local/nagios/libexec/check_portal_health.py
   ```
5. Verify configuration syntax:
   ```bash
   sudo /usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg
   # Ensure 0 errors and 0 warnings
   ```
6. Restart Nagios Core:
   ```bash
   sudo systemctl restart nagios
   ```
7. Open `http://192.168.56.30/nagios` in your browser (login: `nagiosadmin` / `admin123`).

---

## 5. Deployment Option C: Local Workstation Simulation Mode

For rapid testing, development, and grading without virtual machines:

### Step 1: Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --port 8000
```

### Step 2: Frontend Setup
In a second terminal:
```bash
cd frontend
npm install
npm run build
npm run preview
```

### Step 3: Run Disaster Simulation
In a third terminal:
```bash
python scripts/disaster_demo.py --mode local-simulate
```
