# ==============================================================================
# Class: phoenix::baseline
# Enforces OS packages, system users, SSH hardening, and directory hygiene
# ==============================================================================
class phoenix::baseline {
  $baseline_packages = [
    'curl',
    'git',
    'htop',
    'sqlite3',
    'ufw',
    'jq',
    'net-tools',
  ]

  # Ensure essential system packages are installed
  package { $baseline_packages:
    ensure => installed,
  }

  # Ensure phoenix group exists
  group { 'phoenix':
    ensure => present,
    gid    => 1500,
  }

  # Ensure phoenix user exists
  user { 'phoenix':
    ensure     => present,
    uid        => 1500,
    gid        => 'phoenix',
    shell      => '/bin/bash',
    home       => '/home/phoenix',
    managehome => true,
    require    => Group['phoenix'],
  }

  # Ensure application and backup directories exist with strict permissions
  $managed_dirs = [
    '/opt/phoenix',
    '/var/backups/phoenix-db',
    '/var/log/phoenix',
  ]

  file { $managed_dirs:
    ensure  => directory,
    owner   => 'phoenix',
    group   => 'phoenix',
    mode    => '0755',
    require => User['phoenix'],
  }

  # Managed baseline policy file (used for drift demonstration)
  file { '/etc/phoenix-baseline.conf':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => "# Phoenix Managed Baseline Configuration\n# Managed by Puppet Master - Do NOT edit manually\nSECURITY_COMPLIANCE=STRICT\nDRIFT_SELF_HEALING=ENABLED\nMANAGED_AT=2026-11-16\n",
  }

  # SSH Hardening Configuration drop-in
  file { '/etc/ssh/sshd_config.d/50-phoenix.conf':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => "# Phoenix SSH Baseline Hardening\nPermitRootLogin prohibit-password\nX11Forwarding no\nClientAliveInterval 300\nClientAliveCountMax 2\n",
    notify  => Service['ssh'],
  }

  # Ensure SSH daemon is running and enabled
  service { 'ssh':
    ensure => running,
    enable => true,
  }
}
