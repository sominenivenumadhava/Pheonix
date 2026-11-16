#!/bin/bash
# ==============================================================================
# Phoenix EC2 User Data - Puppet Master Bootstrap
# Installs Puppet Server and prepares CA
# ==============================================================================
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y openjdk-11-jre-headless curl git jq wget

wget https://apt.puppet.com/puppet7-release-jammy.deb -O /tmp/puppet7-release.deb
dpkg -i /tmp/puppet7-release.deb
apt-get update -y
apt-get install -y puppetserver

# Configure memory settings for t3.small (1.5GB Heap)
sed -i 's/-Xms2g -Xmx2g/-Xms1g -Xmx1g/' /etc/default/puppetserver

systemctl enable puppetserver || true

echo "--- Puppet Master Bootstrap Completed ---"
