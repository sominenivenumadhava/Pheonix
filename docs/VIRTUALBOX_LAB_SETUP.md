# Phoenix VirtualBox Multi-Node Lab Setup Guide

This guide provides the exact, step-by-step instructions for creating the four Ubuntu 22.04/24.04 virtual machines on Oracle VirtualBox, configuring dual network adapters (NAT + Host-Only), setting static IPs, and distributing SSH keys for Ansible and Puppet automation.

---

## 1. Network Architecture & IP Allocation

| VM Name | Role | RAM | vCPU | Disk | Adapter 1 (Internet) | Adapter 2 (Host-Only Static IP) |
|---|---|---|---|---|---|---|
| **control-node** | Ansible & Terraform Control | 2 GB | 1 | 20 GB | NAT | `192.168.56.10` |
| **puppet-master** | Puppet Server & CA Master | 3 GB | 2 | 20 GB | NAT | `192.168.56.20` |
| **app-server** | Nginx, FastAPI Backend, SQLite, React | 2 GB | 1 | 20 GB | NAT | `192.168.56.30` |
| **nagios-server** | Nagios Core 4.x & Monitoring Plugins | 2 GB | 1 | 20 GB | NAT | `192.168.56.40` |

---

## 2. VirtualBox Host-Only Network Setup

Before creating VMs, ensure the VirtualBox Host-Only network adapter exists:
1. Open **VirtualBox Manager** $\to$ **Tools** $\to$ **Network Manager** (or **Host Network Manager**).
2. Click **Create** to create a host-only network (typically named `vboxnet0` on Linux/macOS or `VirtualBox Host-Only Ethernet Adapter` on Windows).
3. Set IPv4 Address: `192.168.56.1`
4. Set IPv4 Network Mask: `255.255.255.0`
5. **DHCP Server**: **Disable** (uncheck "Enable Server" so we use deterministic static Netplan IPs).

---

## 3. Creating the Virtual Machines

Repeat these steps for each of the 4 VMs using Ubuntu 22.04 LTS (or 24.04 LTS) Server ISO:

### Step 3.1: Hardware & General Settings
- **OS Type**: Linux / Ubuntu (64-bit)
- **Base Memory**: Set per table above (2048 MB for app, control, nagios; 3072 MB for puppet-master).
- **Processors**: 1 vCPU (2 vCPUs for puppet-master).
- **Hard Disk**: Create virtual hard disk (VDI, dynamically allocated, 20 GB).

### Step 3.2: Configure Dual Network Adapters
Under VM **Settings** $\to$ **Network**:
- **Adapter 1**:
  - Attached to: **NAT**
  - Cable Connected: Checked
  *(Provides outbound internet access for apt downloads)*
- **Adapter 2**:
  - Enable Network Adapter: Checked
  - Attached to: **Host-only Adapter**
  - Name: Select `VirtualBox Host-Only Ethernet Adapter` (or `vboxnet0`)
  - Promiscuous Mode: Allow All (or Deny)
  - Cable Connected: Checked

---

## 4. Ubuntu OS Installation & Static IP (Netplan)

1. Boot each VM and install Ubuntu Server. Use `ubuntu` as the default username and password.
2. Once logged in, configure static IP on Adapter 2 via Netplan:

```bash
sudo nano /etc/netplan/01-netcfg.yaml
```

Paste the configuration matching the VM's static IP:

### Example: On `app-server` (`192.168.56.30`):
```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s3:
      dhcp4: true
    enp0s8:
      dhcp4: no
      addresses:
        - 192.168.56.30/24
```
*(Note: Interface names may be `enp0s3` and `enp0s8` or `eth0` and `eth1`. Verify via `ip link`.)*

Apply the network configuration:
```bash
sudo netplan apply
```

Test reachability:
```bash
ip addr show enp0s8
ping -c 2 192.168.56.1
```

---

## 5. SSH Key Setup & Passwordless Sudo

Ansible requires passwordless SSH access and passwordless `sudo` execution.

### Step 5.1: Enable Passwordless Sudo on All 4 VMs
On each VM, run:
```bash
echo "ubuntu ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ubuntu
sudo chmod 0440 /etc/sudoers.d/ubuntu
```

### Step 5.2: Generate & Distribute SSH Keys
On your **Control Node** (or host machine terminal):

1. Generate SSH key pair:
```bash
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""
```

2. Copy public key to all VMs:
```bash
ssh-copy-id ubuntu@192.168.56.10
ssh-copy-id ubuntu@192.168.56.20
ssh-copy-id ubuntu@192.168.56.30
ssh-copy-id ubuntu@192.168.56.40
```

3. Verify passwordless SSH login:
```bash
ssh ubuntu@192.168.56.30 "hostname -I"
```

---

## 6. Running Ansible Deployment

Once the VMs are reachable, run the Ansible deployment from the control node:

```bash
cd phoenix/ansible

# 1. Check syntax
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --syntax-check

# 2. Ping all nodes
ansible -i inventory/hosts.ini phoenix_nodes -m ping

# 3. Deploy full stack
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```
