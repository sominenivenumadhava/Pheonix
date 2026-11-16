# ==============================================================================
# Class: phoenix
# Main entrypoint class for Phoenix module
# ==============================================================================
class phoenix (
  String $db_path = '/opt/phoenix/backend/phoenix.db',
  String $backup_dir = '/var/backups/phoenix-db',
  Boolean $enable_monitoring = true,
) {
  # Validate database path using custom Puppet function
  phoenix::validate_db_path($db_path)

  include phoenix::baseline

  if $enable_monitoring {
    include phoenix::monitoring
  }
}
