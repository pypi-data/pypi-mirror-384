# Advanced filtering and transformation examples

# Filter by prefix with case-sensitive matching
data "pyvider_env_variables" "app_config_sensitive" {
  prefix = "MYAPP_"
  case_sensitive = true
}

# Filter by prefix with case-insensitive matching
data "pyvider_env_variables" "app_config_insensitive" {
  prefix = "myapp_"
  case_sensitive = false  # Matches MYAPP_, MyApp_, myapp_, etc.
}

# Apply transformations to keys and values
data "pyvider_env_variables" "transformed_vars" {
  prefix = "CONFIG_"
  transform_keys = "lower"    # CONFIG_DATABASE_URL becomes config_database_url
  transform_values = "upper"  # Transform all values to uppercase
}

# Complex regex patterns
data "pyvider_env_variables" "url_vars" {
  regex = ".*_URL$"  # Matches any variable ending in _URL
}

data "pyvider_env_variables" "port_vars" {
  regex = ".*PORT.*"  # Matches variables containing PORT anywhere
}

data "pyvider_env_variables" "credential_vars" {
  regex = ".*(KEY|SECRET|TOKEN|PASSWORD).*"  # Security-related variables
}

# Include empty variables
data "pyvider_env_variables" "with_empty" {
  prefix = "OPTIONAL_"
  exclude_empty = false  # Include variables that exist but are empty
}

# Exclude empty variables (default behavior)
data "pyvider_env_variables" "without_empty" {
  prefix = "OPTIONAL_"
  exclude_empty = true
}

# Multiple filtering approaches combined
locals {
  # Combine different filtering results
  all_urls = merge(
    data.pyvider_env_variables.url_vars.values,
    {for k, v in data.pyvider_env_variables.app_config_sensitive.values : k => v if can(regex(".*_URL$", k))}
  )

  # Transform app config variables to a more usable format
  app_config = {
    for key, value in data.pyvider_env_variables.transformed_vars.values :
    replace(replace(key, "config_", ""), "_", ".") => lower(value)
  }

  # Categorize variables by type
  variable_categories = {
    urls = {
      for k, v in data.pyvider_env_variables.url_vars.values : k => v
    }
    ports = {
      for k, v in data.pyvider_env_variables.port_vars.values : k => {
        value = v
        parsed_port = can(tonumber(v)) ? tonumber(v) : null
        is_valid_port = can(tonumber(v)) && tonumber(v) > 0 && tonumber(v) <= 65535
      }
    }
    credentials = {
      for k, v in data.pyvider_env_variables.credential_vars.values : k => {
        length = length(v)
        has_value = v != ""
      }
    }
  }
}

# Create configuration files using filtered variables
resource "pyvider_file_content" "network_config" {
  filename = "/tmp/network_config.yaml"
  content = yamlencode({
    services = {
      for url_key, url_value in local.all_urls :
      replace(lower(url_key), "_url", "") => {
        url = url_value
        type = can(regex("^https?://", url_value)) ? "http" : (
          can(regex("^postgresql://", url_value)) ? "database" : (
            can(regex("^redis://", url_value)) ? "cache" : "unknown"
          )
        )
      }
    }
    ports = {
      for port_key, port_data in local.variable_categories.ports :
      lower(port_key) => {
        value = port_data.value
        number = port_data.parsed_port
        valid = port_data.is_valid_port
      }
    }
    generated_at = timestamp()
  })
}

resource "pyvider_file_content" "app_settings" {
  filename = "/tmp/app_settings.ini"
  content = join("\n", concat(
    ["# Application Settings from Environment Variables", ""],
    [for key, value in local.app_config : "${key} = ${value}"],
    ["", "# Transformation applied:", "# - Keys: lowercased, CONFIG_ prefix removed, underscores to dots", "# - Values: lowercased"]
  ))
}

# Create a summary of filtering results
resource "pyvider_file_content" "filtering_report" {
  filename = "/tmp/filtering_report.md"
  content = templatefile("${path.module}/filtering_report.md.tpl", {
    case_sensitive_count = length(data.pyvider_env_variables.app_config_sensitive.values)
    case_insensitive_count = length(data.pyvider_env_variables.app_config_insensitive.values)
    transformed_count = length(data.pyvider_env_variables.transformed_vars.values)
    url_vars_count = length(data.pyvider_env_variables.url_vars.values)
    port_vars_count = length(data.pyvider_env_variables.port_vars.values)
    credential_vars_count = length(data.pyvider_env_variables.credential_vars.values)
    with_empty_count = length(data.pyvider_env_variables.with_empty.values)
    without_empty_count = length(data.pyvider_env_variables.without_empty.values)

    case_sensitive_vars = keys(data.pyvider_env_variables.app_config_sensitive.values)
    case_insensitive_vars = keys(data.pyvider_env_variables.app_config_insensitive.values)
    url_vars = keys(data.pyvider_env_variables.url_vars.values)
    port_vars = keys(data.pyvider_env_variables.port_vars.values)
    credential_vars = keys(data.pyvider_env_variables.credential_vars.values)

    app_config = local.app_config
    variable_categories = local.variable_categories
  })
}

# Alternative approach without external template file
resource "pyvider_file_content" "filtering_summary" {
  filename = "/tmp/filtering_summary.json"
  content = jsonencode({
    filtering_results = {
      case_sensitive = {
        pattern = "MYAPP_"
        count = length(data.pyvider_env_variables.app_config_sensitive.values)
        variables = keys(data.pyvider_env_variables.app_config_sensitive.values)
      }
      case_insensitive = {
        pattern = "myapp_"
        count = length(data.pyvider_env_variables.app_config_insensitive.values)
        variables = keys(data.pyvider_env_variables.app_config_insensitive.values)
      }
      regex_filters = {
        urls = {
          pattern = ".*_URL$"
          count = length(data.pyvider_env_variables.url_vars.values)
          variables = keys(data.pyvider_env_variables.url_vars.values)
        }
        ports = {
          pattern = ".*PORT.*"
          count = length(data.pyvider_env_variables.port_vars.values)
          variables = keys(data.pyvider_env_variables.port_vars.values)
        }
        credentials = {
          pattern = ".*(KEY|SECRET|TOKEN|PASSWORD).*"
          count = length(data.pyvider_env_variables.credential_vars.values)
          variables = keys(data.pyvider_env_variables.credential_vars.values)
        }
      }
      transformations = {
        keys_lowercased = keys(data.pyvider_env_variables.transformed_vars.values)
        processed_config = local.app_config
      }
      empty_handling = {
        with_empty = length(data.pyvider_env_variables.with_empty.values)
        without_empty = length(data.pyvider_env_variables.without_empty.values)
      }
    }
    categorized_variables = local.variable_categories
    timestamp = timestamp()
  })
}

output "filtering_results" {
  description = "Results of various filtering and transformation approaches"
  value = {
    case_sensitivity = {
      sensitive_match = length(data.pyvider_env_variables.app_config_sensitive.values)
      insensitive_match = length(data.pyvider_env_variables.app_config_insensitive.values)
    }

    regex_patterns = {
      url_matches = length(data.pyvider_env_variables.url_vars.values)
      port_matches = length(data.pyvider_env_variables.port_vars.values)
      credential_matches = length(data.pyvider_env_variables.credential_vars.values)
    }

    transformations = {
      transformed_variables = length(data.pyvider_env_variables.transformed_vars.values)
      processed_config_keys = length(local.app_config)
    }

    empty_variable_handling = {
      including_empty = length(data.pyvider_env_variables.with_empty.values)
      excluding_empty = length(data.pyvider_env_variables.without_empty.values)
    }

    categorized_data = {
      total_urls = length(local.all_urls)
      valid_ports = length([for k, v in local.variable_categories.ports : k if v.is_valid_port])
      credentials_with_values = length([for k, v in local.variable_categories.credentials : k if v.has_value])
    }

    generated_files = [
      pyvider_file_content.network_config.filename,
      pyvider_file_content.app_settings.filename,
      pyvider_file_content.filtering_summary.filename
    ]
  }
}