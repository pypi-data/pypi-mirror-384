# Basic lens_jq function examples

# Simple data extraction
locals {
  # Sample JSON data for demonstration
  user_data = {
    id = 123
    name = "Alice Johnson"
    email = "alice@example.com"
    profile = {
      age = 30
      city = "New York"
      preferences = {
        theme = "dark"
        language = "en"
        notifications = true
      }
    }
    roles = ["user", "moderator"]
    metadata = {
      created_at = "2024-01-15T10:30:00Z"
      last_login = "2024-01-20T14:22:15Z"
      login_count = 42
    }
  }

  # Basic field extraction
  user_name = provider::pyvider::lens_jq(local.user_data, ".name")
  user_email = provider::pyvider::lens_jq(local.user_data, ".email")
  user_id = provider::pyvider::lens_jq(local.user_data, ".id")

  # Nested field extraction
  user_age = provider::pyvider::lens_jq(local.user_data, ".profile.age")
  user_city = provider::pyvider::lens_jq(local.user_data, ".profile.city")
  user_theme = provider::pyvider::lens_jq(local.user_data, ".profile.preferences.theme")

  # Array access
  first_role = provider::pyvider::lens_jq(local.user_data, ".roles[0]")
  second_role = provider::pyvider::lens_jq(local.user_data, ".roles[1]")
  all_roles = provider::pyvider::lens_jq(local.user_data, ".roles")
}

# Complex data transformation
locals {
  # Sample API response data
  api_response = {
    status = "success"
    data = {
      users = [
        {
          id = 1
          name = "Alice"
          email = "alice@example.com"
          active = true
          department = "Engineering"
          salary = 85000
        },
        {
          id = 2
          name = "Bob"
          email = "bob@example.com"
          active = true
          department = "Marketing"
          salary = 65000
        },
        {
          id = 3
          name = "Charlie"
          email = "charlie@example.com"
          active = false
          department = "Engineering"
          salary = 90000
        }
      ]
      metadata = {
        total_count = 3
        page = 1
        per_page = 10
      }
    }
  }

  # Extract specific information
  all_users = provider::pyvider::lens_jq(local.api_response, ".data.users")
  active_users = provider::pyvider::lens_jq(local.api_response, ".data.users | map(select(.active == true))")
  engineering_users = provider::pyvider::lens_jq(local.api_response, ".data.users | map(select(.department == \"Engineering\"))")

  # Extract names only
  all_names = provider::pyvider::lens_jq(local.api_response, ".data.users | map(.name)")
  active_names = provider::pyvider::lens_jq(local.api_response, ".data.users | map(select(.active == true)) | map(.name)")

  # Calculate aggregates
  total_salary = provider::pyvider::lens_jq(local.api_response, ".data.users | map(.salary) | add")
  average_salary = provider::pyvider::lens_jq(local.api_response, ".data.users | map(.salary) | add / length")
  max_salary = provider::pyvider::lens_jq(local.api_response, ".data.users | map(.salary) | max")
  min_salary = provider::pyvider::lens_jq(local.api_response, ".data.users | map(.salary) | min")
}

# Configuration processing
variable "app_config" {
  type = map(any)
  default = {
    database = {
      connections = [
        {
          name = "primary"
          host = "db1.example.com"
          port = 5432
          ssl = true
          pool_size = 20
        },
        {
          name = "replica"
          host = "db2.example.com"
          port = 5432
          ssl = true
          pool_size = 10
        },
        {
          name = "analytics"
          host = "analytics-db.example.com"
          port = 5432
          ssl = false
          pool_size = 5
        }
      ]
    }
    services = {
      api = {
        host = "api.example.com"
        port = 8080
        instances = 3
      }
      worker = {
        host = "worker.example.com"
        port = 8081
        instances = 2
      }
    }
  }
}

locals {
  # Extract database connection information
  primary_db = provider::pyvider::lens_jq(var.app_config, ".database.connections | map(select(.name == \"primary\")) | .[0]")
  ssl_enabled_dbs = provider::pyvider::lens_jq(var.app_config, ".database.connections | map(select(.ssl == true))")
  total_pool_size = provider::pyvider::lens_jq(var.app_config, ".database.connections | map(.pool_size) | add")

  # Extract service information
  api_instances = provider::pyvider::lens_jq(var.app_config, ".services.api.instances")
  worker_instances = provider::pyvider::lens_jq(var.app_config, ".services.worker.instances")
  total_instances = provider::pyvider::lens_jq(var.app_config, ".services | [.api.instances, .worker.instances] | add")

  # Create connection strings
  db_hosts = provider::pyvider::lens_jq(var.app_config, ".database.connections | map(.host)")
  service_endpoints = provider::pyvider::lens_jq(var.app_config, ".services | to_entries | map(\"\\(.key)://\\(.value.host):\\(.value.port)\")")
}

# Log analysis
locals {
  # Sample log data
  log_entries = [
    {
      timestamp = "2024-01-15T10:30:15Z"
      level = "INFO"
      message = "Application started"
      user_id = null
      request_id = "req-001"
    },
    {
      timestamp = "2024-01-15T10:30:16Z"
      level = "DEBUG"
      message = "Database connection established"
      user_id = null
      request_id = "req-001"
    },
    {
      timestamp = "2024-01-15T10:31:20Z"
      level = "INFO"
      message = "User login successful"
      user_id = 123
      request_id = "req-002"
    },
    {
      timestamp = "2024-01-15T10:32:10Z"
      level = "WARN"
      message = "Rate limit exceeded"
      user_id = 456
      request_id = "req-003"
    },
    {
      timestamp = "2024-01-15T10:33:05Z"
      level = "ERROR"
      message = "Database query failed"
      user_id = 123
      request_id = "req-004"
    }
  ]

  # Analyze log data
  error_logs = provider::pyvider::lens_jq(local.log_entries, "map(select(.level == \"ERROR\"))")
  warning_logs = provider::pyvider::lens_jq(local.log_entries, "map(select(.level == \"WARN\"))")
  user_related_logs = provider::pyvider::lens_jq(local.log_entries, "map(select(.user_id != null))")

  # Extract specific information
  error_messages = provider::pyvider::lens_jq(local.log_entries, "map(select(.level == \"ERROR\")) | map(.message)")
  unique_users = provider::pyvider::lens_jq(local.log_entries, "map(.user_id) | map(select(. != null)) | unique")
  log_levels = provider::pyvider::lens_jq(local.log_entries, "map(.level) | unique")

  # Count statistics
  error_count = provider::pyvider::lens_jq(local.log_entries, "map(select(.level == \"ERROR\")) | length")
  warning_count = provider::pyvider::lens_jq(local.log_entries, "map(select(.level == \"WARN\")) | length")
  total_logs = provider::pyvider::lens_jq(local.log_entries, "length")
}

# Create analysis reports
resource "pyvider_file_content" "user_analysis" {
  filename = "/tmp/user_analysis.json"
  content = jsonencode({
    user_profile = {
      name = local.user_name
      email = local.user_email
      age = local.user_age
      city = local.user_city
      theme = local.user_theme
      roles = local.all_roles
    }
    extracted_at = timestamp()
  })
}

resource "pyvider_file_content" "team_analysis" {
  filename = "/tmp/team_analysis.json"
  content = jsonencode({
    summary = {
      total_users = length(local.all_users)
      active_users = length(local.active_users)
      engineering_team = length(local.engineering_users)
    }
    salary_analysis = {
      total = local.total_salary
      average = local.average_salary
      max = local.max_salary
      min = local.min_salary
    }
    names = {
      all = local.all_names
      active_only = local.active_names
    }
    generated_at = timestamp()
  })
}

resource "pyvider_file_content" "config_analysis" {
  filename = "/tmp/config_analysis.json"
  content = jsonencode({
    database = {
      primary_connection = local.primary_db
      ssl_enabled_count = length(local.ssl_enabled_dbs)
      total_pool_size = local.total_pool_size
      hosts = local.db_hosts
    }
    services = {
      api_instances = local.api_instances
      worker_instances = local.worker_instances
      total_instances = local.total_instances
      endpoints = local.service_endpoints
    }
    analyzed_at = timestamp()
  })
}

resource "pyvider_file_content" "log_analysis" {
  filename = "/tmp/log_analysis.json"
  content = jsonencode({
    statistics = {
      total_logs = local.total_logs
      error_count = local.error_count
      warning_count = local.warning_count
    }
    levels_found = local.log_levels
    unique_users = local.unique_users
    error_messages = local.error_messages
    sample_logs = {
      errors = local.error_logs
      warnings = local.warning_logs
      user_related = local.user_related_logs
    }
    analyzed_at = timestamp()
  })
}

# Output lens operations results
output "lens_jq_examples" {
  value = {
    user_extraction = {
      name = local.user_name
      email = local.user_email
      age = local.user_age
      roles = local.all_roles
      analysis_file = pyvider_file_content.user_analysis.filename
    }

    team_analysis = {
      total_users = length(local.all_users)
      active_count = length(local.active_users)
      engineering_count = length(local.engineering_users)
      salary_stats = {
        total = local.total_salary
        average = local.average_salary
        range = "${local.min_salary} - ${local.max_salary}"
      }
      analysis_file = pyvider_file_content.team_analysis.filename
    }

    configuration = {
      database_pools = local.total_pool_size
      service_instances = local.total_instances
      ssl_connections = length(local.ssl_enabled_dbs)
      analysis_file = pyvider_file_content.config_analysis.filename
    }

    log_analysis = {
      total_entries = local.total_logs
      errors = local.error_count
      warnings = local.warning_count
      unique_users = length(local.unique_users)
      analysis_file = pyvider_file_content.log_analysis.filename
    }
  }
}