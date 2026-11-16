# ==============================================================================
# Class: phoenix::web
# Installs and manages Nginx, ensures virtual host template, and manages service
# ==============================================================================
class phoenix::web {
  package { 'nginx':
    ensure => installed,
  }

  file { '/var/www/phoenix':
    ensure  => directory,
    owner   => 'www-data',
    group   => 'www-data',
    mode    => '0755',
    require => Package['nginx'],
  }

  # Deploy compiled virtual host from ERB template
  file { '/etc/nginx/sites-available/phoenix':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('phoenix/nginx_vhost.conf.erb'),
    require => Package['nginx'],
    notify  => Service['nginx'],
  }

  # Remove default virtual host if present
  file { '/etc/nginx/sites-enabled/default':
    ensure => absent,
    notify => Service['nginx'],
  }

  # Enable phoenix virtual host
  file { '/etc/nginx/sites-enabled/phoenix':
    ensure  => link,
    target  => '/etc/nginx/sites-available/phoenix',
    require => File['/etc/nginx/sites-available/phoenix'],
    notify  => Service['nginx'],
  }

  # Ensure Nginx service is running and enabled
  service { 'nginx':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    require    => Package['nginx'],
  }
}
