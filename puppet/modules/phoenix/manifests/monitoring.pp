# ==============================================================================
# Class: phoenix::monitoring
# Provisions NRPE monitoring daemon and Nagios remote plugins
# ==============================================================================
class phoenix::monitoring {
  $monitoring_packages = [
    'nagios-nrpe-server',
    'monitoring-plugins-basic',
    'monitoring-plugins-common',
  ]

  package { $monitoring_packages:
    ensure => installed,
  }

  file { '/etc/nagios/nrpe.cfg':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('phoenix/nrpe.cfg.erb'),
    require => Package['nagios-nrpe-server'],
    notify  => Service['nagios-nrpe-server'],
  }

  service { 'nagios-nrpe-server':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    require    => Package['nagios-nrpe-server'],
  }
}
