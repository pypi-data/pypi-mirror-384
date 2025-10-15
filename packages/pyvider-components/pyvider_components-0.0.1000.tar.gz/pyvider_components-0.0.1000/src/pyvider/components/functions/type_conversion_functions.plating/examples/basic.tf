# Basic type conversion function examples

# String conversion from various types
locals {
  # Number to string conversions
  integer_value = 42
  float_value = 3.14159
  negative_value = -100

  int_to_string = provider::pyvider::tostring(local.integer_value)     # Returns: "42"
  float_to_string = provider::pyvider::tostring(local.float_value)     # Returns: "3.14159"
  negative_to_string = provider::pyvider::tostring(local.negative_value) # Returns: "-100"

  # Boolean to string conversions
  true_value = true
  false_value = false

  true_to_string = provider::pyvider::tostring(local.true_value)       # Returns: "true"
  false_to_string = provider::pyvider::tostring(local.false_value)     # Returns: "false"

  # List to string conversions
  simple_list = [1, 2, 3]
  string_list = ["apple", "banana", "cherry"]
  mixed_list = [1, "two", true]

  simple_list_string = provider::pyvider::tostring(local.simple_list)  # Returns: "[1, 2, 3]"
  string_list_string = provider::pyvider::tostring(local.string_list)  # Returns: '["apple", "banana", "cherry"]'
  mixed_list_string = provider::pyvider::tostring(local.mixed_list)    # Returns: '[1, "two", true]'

  # Map to string conversions
  simple_map = {
    name = "Alice"
    age = 30
  }
  nested_map = {
    user = {
      name = "Bob"
      details = {
        age = 25
        active = true
      }
    }
  }

  simple_map_string = provider::pyvider::tostring(local.simple_map)    # Returns: '{"age": 30, "name": "Alice"}'
  nested_map_string = provider::pyvider::tostring(local.nested_map)    # Returns: nested JSON structure
}

# Practical use cases for string conversion
variable "server_config" {
  type = object({
    host     = string
    port     = number
    ssl      = bool
    timeouts = list(number)
    metadata = map(string)
  })
  default = {
    host     = "api.example.com"
    port     = 8080
    ssl      = true
    timeouts = [30, 60, 120]
    metadata = {
      environment = "production"
      version     = "1.2.3"
    }
  }
}

locals {
  # Convert configuration values to strings for logging/display
  config_strings = {
    host_info = "Server: ${var.server_config.host}:${provider::pyvider::tostring(var.server_config.port)}"
    ssl_status = "SSL Enabled: ${provider::pyvider::tostring(var.server_config.ssl)}"
    timeout_list = "Timeouts: ${provider::pyvider::tostring(var.server_config.timeouts)}"
    metadata_json = "Metadata: ${provider::pyvider::tostring(var.server_config.metadata)}"
  }

  # Create a formatted configuration summary
  config_summary = join("\n", [
    "=== Server Configuration ===",
    local.config_strings.host_info,
    local.config_strings.ssl_status,
    local.config_strings.timeout_list,
    local.config_strings.metadata_json
  ])
}

# Environment variable preparation
variable "app_settings" {
  type = object({
    debug_mode      = bool
    max_connections = number
    allowed_hosts   = list(string)
    database_config = map(any)
  })
  default = {
    debug_mode      = false
    max_connections = 100
    allowed_hosts   = ["localhost", "api.example.com"]
    database_config = {
      host     = "db.example.com"
      port     = 5432
      ssl_mode = "require"
    }
  }
}

locals {
  # Convert various types to strings for environment variables
  env_vars = {
    DEBUG_MODE      = provider::pyvider::tostring(var.app_settings.debug_mode)
    MAX_CONNECTIONS = provider::pyvider::tostring(var.app_settings.max_connections)
    ALLOWED_HOSTS   = provider::pyvider::tostring(var.app_settings.allowed_hosts)
    DATABASE_CONFIG = provider::pyvider::tostring(var.app_settings.database_config)
  }

  # Create .env file content
  env_file_content = join("\n", [
    for key, value in local.env_vars :
    "${key}=${value}"
  ])
}

# API response formatting
variable "user_data" {
  type = list(object({
    id       = number
    username = string
    active   = bool
    roles    = list(string)
    profile  = map(any)
  }))
  default = [
    {
      id       = 1
      username = "alice"
      active   = true
      roles    = ["user", "admin"]
      profile = {
        email     = "alice@example.com"
        last_login = "2024-01-15T10:30:00Z"
      }
    },
    {
      id       = 2
      username = "bob"
      active   = false
      roles    = ["user"]
      profile = {
        email = "bob@example.com"
      }
    }
  ]
}

locals {
  # Convert user data to JSON strings for API responses
  user_json_strings = [
    for user in var.user_data : {
      id_string       = provider::pyvider::tostring(user.id)
      username        = user.username  # Already a string
      active_string   = provider::pyvider::tostring(user.active)
      roles_string    = provider::pyvider::tostring(user.roles)
      profile_string  = provider::pyvider::tostring(user.profile)
      full_json       = provider::pyvider::tostring(user)
    }
  ]

  # Create a user summary report
  user_summary = join("\n", concat(
    ["=== User Data Summary ===", ""],
    flatten([
      for idx, user in var.user_data : [
        "User ${provider::pyvider::tostring(user.id)}:",
        "  Username: ${user.username}",
        "  Active: ${provider::pyvider::tostring(user.active)}",
        "  Roles: ${provider::pyvider::tostring(user.roles)}",
        "  Profile: ${provider::pyvider::tostring(user.profile)}",
        ""
      ]
    ])
  ))
}

# Logging and debugging
variable "system_metrics" {
  type = object({
    cpu_usage    = number
    memory_usage = number
    disk_usage   = number
    uptime       = number
    alerts       = list(string)
    status       = map(bool)
  })
  default = {
    cpu_usage    = 75.5
    memory_usage = 82.3
    disk_usage   = 45.7
    uptime       = 86400
    alerts       = ["high_memory", "disk_cleanup_needed"]
    status = {
      healthy     = true
      maintenance = false
      backup_running = true
    }
  }
}

locals {
  # Convert metrics to strings for logging
  metric_strings = {
    cpu    = "CPU: ${provider::pyvider::tostring(var.system_metrics.cpu_usage)}%"
    memory = "Memory: ${provider::pyvider::tostring(var.system_metrics.memory_usage)}%"
    disk   = "Disk: ${provider::pyvider::tostring(var.system_metrics.disk_usage)}%"
    uptime = "Uptime: ${provider::pyvider::tostring(var.system_metrics.uptime)} seconds"
    alerts = "Alerts: ${provider::pyvider::tostring(var.system_metrics.alerts)}"
    status = "Status: ${provider::pyvider::tostring(var.system_metrics.status)}"
  }

  # Create formatted log entry
  log_entry = join(" | ", [
    "METRICS",
    local.metric_strings.cpu,
    local.metric_strings.memory,
    local.metric_strings.disk,
    local.metric_strings.uptime,
    "Alerts: ${length(var.system_metrics.alerts)}"
  ])
}

# Create output files with converted strings
resource "pyvider_file_content" "config_summary" {
  filename = "/tmp/server_config_summary.txt"
  content  = local.config_summary
}

resource "pyvider_file_content" "environment_vars" {
  filename = "/tmp/application.env"
  content  = local.env_file_content
}

resource "pyvider_file_content" "user_report" {
  filename = "/tmp/user_data_report.txt"
  content  = local.user_summary
}

resource "pyvider_file_content" "system_log" {
  filename = "/tmp/system_metrics.log"
  content = join("\n", [
    "=== System Metrics Log ===",
    "",
    "Timestamp: ${timestamp()}",
    local.log_entry,
    "",
    "Detailed Status:",
    local.metric_strings.status,
    "",
    "Active Alerts:",
    local.metric_strings.alerts
  ])
}

# Output conversion examples
output "type_conversion_examples" {
  value = {
    basic_conversions = {
      numbers = {
        integer = {
          original = local.integer_value
          converted = local.int_to_string
        }
        float = {
          original = local.float_value
          converted = local.float_to_string
        }
        negative = {
          original = local.negative_value
          converted = local.negative_to_string
        }
      }

      booleans = {
        true_value = {
          original = local.true_value
          converted = local.true_to_string
        }
        false_value = {
          original = local.false_value
          converted = local.false_to_string
        }
      }

      collections = {
        simple_list = {
          original = local.simple_list
          converted = local.simple_list_string
        }
        string_list = {
          original = local.string_list
          converted = local.string_list_string
        }
        simple_map = {
          original = local.simple_map
          converted = local.simple_map_string
        }
      }
    }

    practical_usage = {
      configuration = {
        summary_file = pyvider_file_content.config_summary.filename
        env_file = pyvider_file_content.environment_vars.filename
      }

      user_management = {
        report_file = pyvider_file_content.user_report.filename
        total_users = length(var.user_data)
      }

      system_monitoring = {
        log_file = pyvider_file_content.system_log.filename
        log_entry = local.log_entry
      }
    }

    conversion_stats = {
      total_conversions = 15  # Approximate count of conversions performed
      file_outputs = 4        # Number of files created with converted data
    }
  }
}