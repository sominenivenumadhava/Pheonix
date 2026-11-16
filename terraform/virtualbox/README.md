# Phoenix VirtualBox Offline Infrastructure

Provides an offline-capable VirtualBox environment matching the AWS EC2 topology.

---

## 1. Quick Start with Vagrant
If you have Vagrant installed alongside VirtualBox:
```bash
cd terraform/virtualbox
vagrant up
```
This spins up all 4 machines (`control-node`, `puppet-master`, `app-server`, `nagios-server`) with static IPs in `192.168.56.0/24`.

To SSH into any machine:
```bash
vagrant ssh app-server
```

To destroy:
```bash
vagrant destroy -f
```

## 2. Manual VirtualBox Setup Alternative
If you prefer not using Vagrant, follow the complete manual installation instructions documented in [`docs/VIRTUALBOX_LAB_SETUP.md`](file:///c:/Users/venum/.gemini/antigravity-ide\scratch\Phoenix\docs\VIRTUALBOX_LAB_SETUP.md).
