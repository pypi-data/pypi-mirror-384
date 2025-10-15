# Sensitive variable handling examples

# Read a mix of sensitive and non-sensitive variables
data "pyvider_env_variables" "app_credentials" {
  keys = [
    "DATABASE_URL",     # Sensitive - contains credentials
    "API_SECRET_KEY",   # Sensitive - secret key
    "JWT_SIGNING_KEY",  # Sensitive - cryptographic key
    "APP_NAME",         # Not sensitive - application name
    "APP_VERSION",      # Not sensitive - version info
    "LOG_LEVEL"         # Not sensitive - logging configuration
  ]

  # Mark which variables should be treated as sensitive
  sensitive_keys = [
    "DATABASE_URL",
    "API_SECRET_KEY",
    "JWT_SIGNING_KEY"
  ]
}

# Read environment variables with prefix filtering for secrets
data "pyvider_env_variables" "secrets" {
  prefix = "SECRET_"
  # All variables with SECRET_ prefix are treated as sensitive
  sensitive_keys = [for k in keys(data.pyvider_env_variables.secrets.all_environment) : k if can(regex("^SECRET_", k))]
}

# Read configuration with selective sensitivity
data "pyvider_env_variables" "oauth_config" {
  prefix = "OAUTH_"
  sensitive_keys = [
    "OAUTH_CLIENT_SECRET",
    "OAUTH_PRIVATE_KEY"
    # OAUTH_CLIENT_ID and OAUTH_REDIRECT_URI are not sensitive
  ]
}

# Example of safely using sensitive variables
locals {
  # Non-sensitive configuration can be used directly
  app_metadata = {
    name     = lookup(data.pyvider_env_variables.app_credentials.values, "APP_NAME", "unknown-app")
    version  = lookup(data.pyvider_env_variables.app_credentials.values, "APP_VERSION", "0.0.0")
    log_level = lookup(data.pyvider_env_variables.app_credentials.values, "LOG_LEVEL", "INFO")
  }

  # For sensitive data, we need to be careful about how we use it
  # We can't directly interpolate sensitive values into strings
  has_database_url = contains(keys(data.pyvider_env_variables.app_credentials.sensitive_values), "DATABASE_URL")
  has_api_key = contains(keys(data.pyvider_env_variables.app_credentials.sensitive_values), "API_SECRET_KEY")

  # OAuth configuration (mixed sensitive/non-sensitive)
  oauth_public_config = {
    client_id = lookup(data.pyvider_env_variables.oauth_config.values, "OAUTH_CLIENT_ID", "")
    redirect_uri = lookup(data.pyvider_env_variables.oauth_config.values, "OAUTH_REDIRECT_URI", "")
    enabled = lookup(data.pyvider_env_variables.oauth_config.values, "OAUTH_ENABLED", "false") == "true"
  }
}

# Create a non-sensitive configuration file
resource "pyvider_file_content" "public_config" {
  filename = "/tmp/public_config.yaml"
  content = yamlencode({
    application = local.app_metadata
    oauth = local.oauth_public_config
    security = {
      has_database_credentials = local.has_database_url
      has_api_key = local.has_api_key
      total_secrets = length(data.pyvider_env_variables.app_credentials.sensitive_values)
    }
    generated_at = timestamp()
  })
}

# Create a template file that references sensitive variables
# Note: The actual sensitive values won't be exposed in the file content
resource "pyvider_file_content" "app_config_template" {
  filename = "/tmp/app_config_template.env"
  content = join("\n", [
    "# Application Configuration Template",
    "# This file shows which environment variables are expected",
    "",
    "# Application Metadata",
    "APP_NAME=${local.app_metadata.name}",
    "APP_VERSION=${local.app_metadata.version}",
    "LOG_LEVEL=${local.app_metadata.log_level}",
    "",
    "# Sensitive Variables (values not shown)",
    "# These must be set in the environment:",
    local.has_database_url ? "# DATABASE_URL=<configured>" : "# DATABASE_URL=<not configured>",
    local.has_api_key ? "# API_SECRET_KEY=<configured>" : "# API_SECRET_KEY=<not configured>",
    "",
    "# OAuth Configuration",
    "OAUTH_CLIENT_ID=${local.oauth_public_config.client_id}",
    "OAUTH_REDIRECT_URI=${local.oauth_public_config.redirect_uri}",
    "OAUTH_ENABLED=${local.oauth_public_config.enabled}",
    "# OAUTH_CLIENT_SECRET=<sensitive>",
    "# OAUTH_PRIVATE_KEY=<sensitive>",
    "",
    "# Configuration generated at: ${timestamp()}"
  ])
}

# Example of secure credential validation
locals {
  # Check if required sensitive variables are present
  required_secrets = ["DATABASE_URL", "API_SECRET_KEY"]
  missing_secrets = [
    for secret in local.required_secrets :
    secret if !contains(keys(data.pyvider_env_variables.app_credentials.sensitive_values), secret)
  ]

  # Validate credential formats (without exposing values)
  credential_validation = {
    database_url_format_valid = local.has_database_url ? (
      can(regex("^(postgresql|mysql|sqlite)://",
        data.pyvider_env_variables.app_credentials.sensitive_values["DATABASE_URL"]
      ))
    ) : false

    api_key_length_valid = local.has_api_key ? (
      length(data.pyvider_env_variables.app_credentials.sensitive_values["API_SECRET_KEY"]) >= 32
    ) : false
  }
}

# Create a security report (without exposing sensitive values)
resource "pyvider_file_content" "security_report" {
  filename = "/tmp/security_report.json"
  content = jsonencode({
    security_assessment = {
      total_variables_checked = length(data.pyvider_env_variables.app_credentials.keys)
      sensitive_variables_found = length(data.pyvider_env_variables.app_credentials.sensitive_values)
      non_sensitive_variables = length(data.pyvider_env_variables.app_credentials.values)

      required_secrets = {
        expected = local.required_secrets
        missing = local.missing_secrets
        all_present = length(local.missing_secrets) == 0
      }

      credential_validation = local.credential_validation

      oauth_config = {
        public_settings = local.oauth_public_config
        sensitive_keys_present = {
          client_secret = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_CLIENT_SECRET")
          private_key = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_PRIVATE_KEY")
        }
      }

      recommendations = concat(
        length(local.missing_secrets) > 0 ? ["Set missing environment variables: ${join(", ", local.missing_secrets)}"] : [],
        !local.credential_validation.database_url_format_valid ? ["Check DATABASE_URL format"] : [],
        !local.credential_validation.api_key_length_valid ? ["API_SECRET_KEY should be at least 32 characters"] : []
      )
    }
    generated_at = timestamp()
  })
}

# Example of conditional resource creation based on sensitive variables
resource "pyvider_file_content" "database_status" {
  count = local.has_database_url ? 1 : 0

  filename = "/tmp/database_available.txt"
  content = join("\n", [
    "Database configuration detected",
    "Application: ${local.app_metadata.name}",
    "Version: ${local.app_metadata.version}",
    "Database URL is configured and available",
    "URL format validation: ${local.credential_validation.database_url_format_valid ? "PASSED" : "FAILED"}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

resource "pyvider_file_content" "no_database_warning" {
  count = !local.has_database_url ? 1 : 0

  filename = "/tmp/no_database_warning.txt"
  content = join("\n", [
    "WARNING: No database configuration found",
    "Application: ${local.app_metadata.name}",
    "Please set the DATABASE_URL environment variable",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "sensitive_variable_handling" {
  description = "Example of handling sensitive environment variables"
  value = {
    application_info = local.app_metadata

    security_status = {
      total_secrets_configured = length(data.pyvider_env_variables.app_credentials.sensitive_values)
      required_secrets_present = length(local.missing_secrets) == 0
      missing_secrets_count = length(local.missing_secrets)
      # Note: We don't expose the actual missing secret names in output
    }

    oauth_status = {
      public_config = local.oauth_public_config
      has_client_secret = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_CLIENT_SECRET")
      has_private_key = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_PRIVATE_KEY")
    }

    validation_results = local.credential_validation

    files_created = {
      public_config = pyvider_file_content.public_config.filename
      template = pyvider_file_content.app_config_template.filename
      security_report = pyvider_file_content.security_report.filename
      database_status = local.has_database_url ? pyvider_file_content.database_status[0].filename : null
      no_database_warning = !local.has_database_url ? pyvider_file_content.no_database_warning[0].filename : null
    }
  }

  # Mark this output as sensitive since it contains information about sensitive variables
  sensitive = true
}