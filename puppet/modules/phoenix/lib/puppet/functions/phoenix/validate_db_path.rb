# frozen_string_literal: true

# ==============================================================================
# Puppet Custom Function: phoenix::validate_db_path
# Validates that SQLite database paths are absolute and have valid extensions.
# ==============================================================================

Puppet::Functions.create_function(:'phoenix::validate_db_path') do
  dispatch :validate_db_path do
    param 'String', :path
    return_type 'Boolean'
  end

  def validate_db_path(path)
    unless path.start_with?('/')
      raise Puppet::ParseError, "phoenix::validate_db_path(): path '#{path}' must be an absolute path starting with '/'"
    end

    valid_extensions = ['.db', '.sqlite', '.sqlite3']
    unless valid_extensions.any? { |ext| path.end_with?(ext) }
      raise Puppet::ParseError, "phoenix::validate_db_path(): path '#{path}' must end with one of #{valid_extensions.join(', ')}"
    end

    true
  end
end
