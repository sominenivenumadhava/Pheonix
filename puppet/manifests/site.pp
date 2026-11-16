# ==============================================================================
# Phoenix Puppet Master Site Manifest (site.pp)
# Class assignments across node roles
# ==============================================================================

# Baseline configuration applied to every managed node
node default {
  include phoenix::baseline
}

# Application Server: Baseline + Web Proxy + NRPE Monitoring Agent
node 'app-server', /.*app-server.*/ {
  include phoenix::baseline
  include phoenix::web
  include phoenix::monitoring
}

# Nagios Server: Baseline + Monitoring Server prerequisites
node 'nagios-server', /.*nagios-server.*/ {
  include phoenix::baseline
}

# Puppet Master Node
node 'puppet-master', /.*puppet-master.*/ {
  include phoenix::baseline
}
