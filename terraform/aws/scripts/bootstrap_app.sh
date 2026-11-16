#!/bin/bash
# ==============================================================================
# Phoenix EC2 User Data - Application Server Bootstrap
# Installs baseline prerequisites for Ansible and Puppet Agent
# ==============================================================================
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "--- Updating Package Cache ---"
apt-get update -y
apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  python3 \
  python3-pip \
  python3-venv \
  git \
  jq \
  sqlite3

echo "--- Installing Puppet Agent ---"
wget https://apt.puppet.com/puppet7-release-jammy.deb -O /tmp/puppet7-release.deb
dpkg -i /tmp/puppet7-release.deb
apt-get update -y
apt-get install -y puppet-agent

# Set up systemd service link
systemctl enable puppet || true

echo "--- App Server Bootstrap Completed ---"
