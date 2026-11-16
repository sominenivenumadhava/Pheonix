#!/usr/bin/env bash
# ==============================================================================
# Phoenix - Nagios Core 4.x Automated Installation Script
# Target: Ubuntu 22.04 LTS / 24.04 LTS on Nagios Server VM (192.168.56.40)
# ==============================================================================
set -euo pipefail

NAGIOS_VER="4.4.14"
PLUGINS_VER="2.4.8"
NAGIOS_PASS="${1:-"AdminPass123!"}"

echo "=================================================="
echo " Phoenix - Installing Nagios Core ${NAGIOS_VER}"
echo "=================================================="

# 1. Install Build Dependencies
echo "[1/7] Installing required dependencies..."
sudo apt-get update -y
sudo apt-get install -y \
  autoconf gcc libc6 make wget unzip apache2 apache2-utils php \
  libgd-dev libmcrypt-dev libssl-dev bc gawk dc build-essential \
  snmp libnet-snmp-perl python3 python3-pip curl git

# 2. Download and Extract Nagios Core
echo "[2/7] Downloading Nagios Core source..."
cd /tmp
wget -q "https://github.com/NagiosEnterprises/nagioscore/releases/download/nagios-${NAGIOS_VER}/nagios-${NAGIOS_VER}.tar.gz"
tar -xzf "nagios-${NAGIOS_VER}.tar.gz"
cd "nagios-${NAGIOS_VER}"

# 3. Compile and Install
echo "[3/7] Compiling Nagios Core..."
./configure --with-httpd-conf=/etc/apache2/sites-enabled
make all
sudo make install-groups-users
sudo usermod -a -G nagios www-data
sudo make install
sudo make install-daemoninit
sudo make install-commandmode
sudo make install-config
sudo make install-webconf

# 4. Configure Apache and Web Authentication
echo "[4/7] Configuring Apache Web UI..."
sudo a2enmod rewrite cgi
sudo htpasswd -b -c /usr/local/nagios/etc/htpasswd.users nagiosadmin "$NAGIOS_PASS"
sudo systemctl restart apache2

# 5. Download and Install Official Nagios Plugins
echo "[5/7] Installing Nagios Monitoring Plugins..."
cd /tmp
wget -q "https://github.com/nagios-plugins/nagios-plugins/releases/download/release-${PLUGINS_VER}/nagios-plugins-${PLUGINS_VER}.tar.gz"
tar -xzf "nagios-plugins-${PLUGINS_VER}.tar.gz"
cd "nagios-plugins-${PLUGINS_VER}"
./configure --with-nagios-user=nagios --with-nagios-group=nagios
make -j$(nproc)
sudo make install

# 6. Deploy Phoenix Custom Configuration and Plugins
echo "[6/7] Deploying Phoenix host/service definitions and custom plugins..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Deploy custom plugins
sudo cp "${SCRIPT_DIR}/plugins/check_portal_health.py" /usr/local/nagios/libexec/
sudo cp "${SCRIPT_DIR}/plugins/check_web_errors.sh" /usr/local/nagios/libexec/
sudo cp "${SCRIPT_DIR}/plugins/check_web_errors.py" /usr/local/nagios/libexec/ 2>/dev/null || true
sudo chmod +x /usr/local/nagios/libexec/check_*

# Deploy configuration files
sudo cp "${SCRIPT_DIR}/etc/nagios.cfg" /usr/local/nagios/etc/
sudo cp -r "${SCRIPT_DIR}/etc/objects/"* /usr/local/nagios/etc/objects/

# 7. Validate Configuration and Start Daemon
echo "[7/7] Verifying Nagios configuration integrity..."
sudo /usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg

sudo systemctl enable --now nagios
sudo systemctl status nagios --no-pager || true

echo "=================================================="
echo " Nagios Core Installation Complete!"
echo " Access Dashboard: http://192.168.56.40/nagios/"
echo " Credentials:      nagiosadmin / ${NAGIOS_PASS}"
echo "=================================================="
