# Basic environment variable access examples

# Read specific environment variables
data "pyvider_env_variables" "system_info" {
  keys = ["USER", "HOME", "PATH", "SHELL"]
}

# Read all variables with a specific prefix
data "pyvider_env_variables" "terraform_vars" {
  prefix = "TF_"
}

# Read variables using regex pattern
data "pyvider_env_variables" "path_vars" {
  regex = ".*PATH.*"  # Matches PATH, LD_LIBRARY_PATH, etc.
}

# Create a system info file using environment variables
resource "pyvider_file_content" "system_info" {
  filename = "/tmp/system_info.txt"
  content = join("\n", [
    "=== System Information ===",
    "User: ${lookup(data.pyvider_env_variables.system_info.values, "USER", "unknown")}",
    "Home: ${lookup(data.pyvider_env_variables.system_info.values, "HOME", "/tmp")}",
    "Shell: ${lookup(data.pyvider_env_variables.system_info.values, "SHELL", "/bin/sh")}",
    "",
    "=== Environment Variables ===",
    "Total system variables found: ${length(data.pyvider_env_variables.system_info.all_environment)}",
    "Terraform variables found: ${length(data.pyvider_env_variables.terraform_vars.values)}",
    "PATH-related variables found: ${length(data.pyvider_env_variables.path_vars.values)}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Example with default values for missing variables
data "pyvider_env_variables" "optional_config" {
  keys = ["DATABASE_URL", "REDIS_URL", "LOG_LEVEL", "DEBUG"]
}

locals {
  # Provide sensible defaults for missing environment variables
  config = {
    database_url = lookup(data.pyvider_env_variables.optional_config.values, "DATABASE_URL", "sqlite:///tmp/app.db")
    redis_url    = lookup(data.pyvider_env_variables.optional_config.values, "REDIS_URL", "redis://localhost:6379")
    log_level    = lookup(data.pyvider_env_variables.optional_config.values, "LOG_LEVEL", "INFO")
    debug_mode   = lookup(data.pyvider_env_variables.optional_config.values, "DEBUG", "false") == "true"
  }
}

# Create application configuration file
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/application.conf"
  content = join("\n", [
    "# Application Configuration",
    "# Generated from environment variables with defaults",
    "",
    "[database]",
    "url = ${local.config.database_url}",
    "",
    "[cache]",
    "url = ${local.config.redis_url}",
    "",
    "[logging]",
    "level = ${local.config.log_level}",
    "debug = ${local.config.debug_mode}",
    "",
    "# Available environment variables:",
    "${join("\n", [for key in keys(data.pyvider_env_variables.optional_config.all_environment) : "# ${key}"])}",
    "",
    "# Configuration last updated: ${timestamp()}"
  ])
}

# Example using lookup with complex logic
locals {
  # Determine if we're in a CI environment
  is_ci = anytrue([
    lookup(data.pyvider_env_variables.system_info.all_environment, "CI", "") == "true",
    lookup(data.pyvider_env_variables.system_info.all_environment, "GITHUB_ACTIONS", "") == "true",
    lookup(data.pyvider_env_variables.system_info.all_environment, "GITLAB_CI", "") == "true",
    lookup(data.pyvider_env_variables.system_info.all_environment, "JENKINS_URL", "") != ""
  ])

  # Get user preference or default
  preferred_editor = lookup(
    data.pyvider_env_variables.system_info.values,
    "EDITOR",
    lookup(data.pyvider_env_variables.system_info.values, "VISUAL", "nano")
  )
}

resource "pyvider_file_content" "environment_analysis" {
  filename = "/tmp/env_analysis.json"
  content = jsonencode({
    environment_type = local.is_ci ? "ci" : "development"
    user_info = {
      username        = lookup(data.pyvider_env_variables.system_info.values, "USER", "unknown")
      home_directory  = lookup(data.pyvider_env_variables.system_info.values, "HOME", "/tmp")
      preferred_shell = lookup(data.pyvider_env_variables.system_info.values, "SHELL", "/bin/sh")
      preferred_editor = local.preferred_editor
    }
    system_info = {
      total_env_vars    = length(data.pyvider_env_variables.system_info.all_environment)
      terraform_vars    = length(data.pyvider_env_variables.terraform_vars.values)
      path_related_vars = length(data.pyvider_env_variables.path_vars.values)
      is_ci_environment = local.is_ci
    }
    application_config = local.config
    timestamp = timestamp()
  })
}

output "basic_examples" {
  description = "Basic environment variable usage examples"
  value = {
    user_info = {
      username = lookup(data.pyvider_env_variables.system_info.values, "USER", "unknown")
      home     = lookup(data.pyvider_env_variables.system_info.values, "HOME", "/tmp")
    }

    environment_stats = {
      total_variables      = length(data.pyvider_env_variables.system_info.all_environment)
      terraform_variables  = length(data.pyvider_env_variables.terraform_vars.values)
      path_variables      = length(data.pyvider_env_variables.path_vars.values)
    }

    application_config = local.config

    ci_detection = {
      is_ci_environment = local.is_ci
      preferred_editor  = local.preferred_editor
    }

    created_files = [
      pyvider_file_content.system_info.filename,
      pyvider_file_content.app_config.filename,
      pyvider_file_content.environment_analysis.filename
    ]
  }
}