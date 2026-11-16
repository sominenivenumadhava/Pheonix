#!/bin/bash
# ==============================================================================
# Phoenix EC2 User Data - Nagios Server Bootstrap
# Installs Apache2, PHP, Python, and build tools
# ==============================================================================
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y \
  autoconf \
  gcc \
  libc6 \
  make \
  wget \
  unzip \
  apache2 \
  apache2-utils \
  php \
  libgd-dev \
  libmcrypt-dev \
  libssl-dev \
  bc \
  gawk \
  dc \
  build-essential \
  snmp \
  libnet-snmp-perl \
  python3 \
  python3-pip \
  curl \
  git

systemctl enable apache2

echo "--- Nagios Server Bootstrap Completed ---"
