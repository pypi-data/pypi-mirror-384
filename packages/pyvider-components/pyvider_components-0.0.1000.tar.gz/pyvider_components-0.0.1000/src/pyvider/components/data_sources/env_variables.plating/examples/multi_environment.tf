# Multi-environment configuration management with environment variables

variable "environment" {
  description = "Target environment for deployment"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

# Read environment-specific variables with prefix
data "pyvider_env_variables" "env_config" {
  prefix = "${upper(var.environment)}_"
  case_sensitive = true
}

# Read common application variables
data "pyvider_env_variables" "app_common" {
  prefix = "APP_"
  sensitive_keys = ["APP_SECRET_KEY", "APP_DATABASE_PASSWORD"]
}

# Read environment-agnostic system variables
data "pyvider_env_variables" "system_config" {
  keys = ["HOSTNAME", "USER", "DEPLOYMENT_ID"]
}

# Read feature flags with environment awareness
data "pyvider_env_variables" "feature_flags" {
  regex = "^(FEATURE_|${upper(var.environment)}_FEATURE_).*"
  transform_keys = "lower"
}

locals {
  # Environment-specific configuration with fallbacks
  env_config = {
    # Database configuration
    database_url = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_DATABASE_URL",
      lookup(data.pyvider_env_variables.app_common.values, "APP_DATABASE_URL", "sqlite:///tmp/${var.environment}.db")
    )

    # Redis configuration
    redis_url = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_REDIS_URL",
      lookup(data.pyvider_env_variables.app_common.values, "APP_REDIS_URL", "redis://localhost:6379/${var.environment == "production" ? "0" : "1"}")
    )

    # API configuration
    api_base_url = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_API_BASE_URL",
      var.environment == "production" ? "https://api.example.com" : "http://localhost:3000"
    )

    # Performance settings
    worker_processes = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_WORKERS",
      var.environment == "production" ? "4" : "2"
    )

    # Security settings
    debug_enabled = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_DEBUG",
      var.environment == "development" ? "true" : "false"
    ) == "true"

    # Logging configuration
    log_level = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_LOG_LEVEL",
      var.environment == "production" ? "ERROR" : (var.environment == "staging" ? "WARN" : "DEBUG")
    )
  }

  # Process feature flags
  feature_flags = {
    for key, value in data.pyvider_env_variables.feature_flags.values :
    replace(replace(key, "feature_", ""), "${var.environment}_feature_", "") => value == "true"
  }

  # Environment-specific defaults
  environment_defaults = {
    development = {
      cache_ttl = "60"
      rate_limit = "1000"
      enable_cors = "true"
      ssl_required = "false"
    }
    staging = {
      cache_ttl = "300"
      rate_limit = "500"
      enable_cors = "true"
      ssl_required = "true"
    }
    production = {
      cache_ttl = "3600"
      rate_limit = "100"
      enable_cors = "false"
      ssl_required = "true"
    }
  }

  # Merge environment-specific settings
  runtime_config = merge(
    local.environment_defaults[var.environment],
    {
      for key, value in data.pyvider_env_variables.env_config.values :
      lower(replace(key, "${upper(var.environment)}_", "")) => value
    }
  )

  # System information
  system_info = {
    hostname = lookup(data.pyvider_env_variables.system_config.values, "HOSTNAME", "unknown")
    user = lookup(data.pyvider_env_variables.system_config.values, "USER", "unknown")
    deployment_id = lookup(data.pyvider_env_variables.system_config.values, "DEPLOYMENT_ID", "local-${formatdate("YYYYMMDD-hhmmss", timestamp())}")
  }
}

# Create environment-specific application configuration
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/config-${var.environment}.yaml"
  content = yamlencode({
    environment = var.environment

    application = {
      name = lookup(data.pyvider_env_variables.app_common.values, "APP_NAME", "my-application")
      version = lookup(data.pyvider_env_variables.app_common.values, "APP_VERSION", "1.0.0")
      debug = local.env_config.debug_enabled
    }

    database = {
      url = local.env_config.database_url
      pool_size = tonumber(local.runtime_config.cache_ttl) / 60  # Derive pool size from cache TTL
    }

    cache = {
      url = local.env_config.redis_url
      ttl = tonumber(local.runtime_config.cache_ttl)
    }

    api = {
      base_url = local.env_config.api_base_url
      rate_limit = tonumber(local.runtime_config.rate_limit)
      cors_enabled = local.runtime_config.enable_cors == "true"
    }

    security = {
      ssl_required = local.runtime_config.ssl_required == "true"
      debug_enabled = local.env_config.debug_enabled
    }

    logging = {
      level = local.env_config.log_level
      structured = var.environment == "production"
    }

    features = local.feature_flags

    performance = {
      worker_processes = tonumber(local.env_config.worker_processes)
      cache_ttl = tonumber(local.runtime_config.cache_ttl)
    }

    deployment = {
      environment = var.environment
      hostname = local.system_info.hostname
      user = local.system_info.user
      deployment_id = local.system_info.deployment_id
      timestamp = timestamp()
    }
  })
}

# Create environment-specific Docker environment file
resource "pyvider_file_content" "docker_env" {
  filename = "/tmp/.env.${var.environment}"
  content = join("\n", concat(
    [
      "# Docker Environment for ${upper(var.environment)}",
      "# Generated at ${timestamp()}",
      "",
      "# Application"
    ],
    [for key, value in data.pyvider_env_variables.app_common.values : "${key}=${value}"],
    [
      "",
      "# Environment-specific configuration"
    ],
    [for key, value in data.pyvider_env_variables.env_config.values : "${key}=${value}"],
    [
      "",
      "# Runtime configuration"
    ],
    [for key, value in local.runtime_config : "${upper(key)}=${value}"],
    [
      "",
      "# Feature flags"
    ],
    [for key, value in local.feature_flags : "FEATURE_${upper(key)}=${value}"],
    [
      "",
      "# System information",
      "HOSTNAME=${local.system_info.hostname}",
      "DEPLOYMENT_USER=${local.system_info.user}",
      "DEPLOYMENT_ID=${local.system_info.deployment_id}",
      "TARGET_ENVIRONMENT=${var.environment}"
    ]
  ))
}

# Create environment comparison report
resource "pyvider_file_content" "environment_comparison" {
  filename = "/tmp/environment-comparison.json"
  content = jsonencode({
    current_environment = var.environment

    configurations = {
      for env in ["development", "staging", "production"] :
      env => merge(
        local.environment_defaults[env],
        {
          expected_variables = [
            "${upper(env)}_DATABASE_URL",
            "${upper(env)}_REDIS_URL",
            "${upper(env)}_API_BASE_URL",
            "${upper(env)}_LOG_LEVEL"
          ]
        }
      )
    }

    current_config = {
      environment_variables = length(data.pyvider_env_variables.env_config.values)
      app_variables = length(data.pyvider_env_variables.app_common.values)
      feature_flags = length(local.feature_flags)
      sensitive_variables = length(data.pyvider_env_variables.app_common.sensitive_values)
    }

    validation = {
      has_database = contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_DATABASE_URL") ||
                    contains(keys(data.pyvider_env_variables.app_common.values), "APP_DATABASE_URL")

      has_api_config = contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_API_BASE_URL")

      has_required_secrets = contains(keys(data.pyvider_env_variables.app_common.sensitive_values), "APP_SECRET_KEY")

      environment_specific_vars = [
        for key in keys(data.pyvider_env_variables.env_config.values) :
        key if can(regex("^${upper(var.environment)}_", key))
      ]
    }

    recommendations = concat(
      !contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_DATABASE_URL") &&
      !contains(keys(data.pyvider_env_variables.app_common.values), "APP_DATABASE_URL") ?
      ["Set ${upper(var.environment)}_DATABASE_URL or APP_DATABASE_URL"] : [],

      !contains(keys(data.pyvider_env_variables.app_common.sensitive_values), "APP_SECRET_KEY") ?
      ["Set APP_SECRET_KEY for encryption"] : [],

      var.environment == "production" && local.env_config.debug_enabled ?
      ["Disable debug mode in production"] : [],

      var.environment == "production" && local.runtime_config.enable_cors == "true" ?
      ["Consider disabling CORS in production"] : []
    )

    generated_at = timestamp()
  })
}

# Environment-specific validation
locals {
  validation_errors = concat(
    # Production-specific validations
    var.environment == "production" ? [
      for condition, message in {
        "debug_enabled" = "Debug mode should be disabled in production"
        "cors_enabled" = "CORS should be restricted in production"
        "weak_rate_limit" = "Rate limit should be restrictive in production"
      } : message if (
        condition == "debug_enabled" && local.env_config.debug_enabled
      ) || (
        condition == "cors_enabled" && local.runtime_config.enable_cors == "true"
      ) || (
        condition == "weak_rate_limit" && tonumber(local.runtime_config.rate_limit) > 200
      )
    ] : [],

    # General validations
    [
      for condition, message in {
        "missing_database" = "Database URL is required"
        "missing_secret" = "Application secret key is required"
      } : message if (
        condition == "missing_database" && !contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_DATABASE_URL") && !contains(keys(data.pyvider_env_variables.app_common.values), "APP_DATABASE_URL")
      ) || (
        condition == "missing_secret" && !contains(keys(data.pyvider_env_variables.app_common.sensitive_values), "APP_SECRET_KEY")
      )
    ]
  )
}

# Create validation report
resource "pyvider_file_content" "validation_report" {
  filename = "/tmp/validation-${var.environment}.txt"
  content = join("\n", concat(
    [
      "Environment Validation Report",
      "============================",
      "Environment: ${var.environment}",
      "Generated: ${timestamp()}",
      ""
    ],
    length(local.validation_errors) == 0 ? [
      "✓ All validations passed",
      "Environment is properly configured"
    ] : [
      "❌ Validation Issues Found:",
      ""
    ],
    [for error in local.validation_errors : "  - ${error}"],
    length(local.validation_errors) > 0 ? ["", "Please address these issues before deployment."] : []
  ))
}

output "multi_environment_config" {
  description = "Multi-environment configuration management results"
  value = {
    environment = var.environment

    configuration_summary = {
      environment_vars = length(data.pyvider_env_variables.env_config.values)
      app_vars = length(data.pyvider_env_variables.app_common.values)
      feature_flags = length(local.feature_flags)
      sensitive_vars = length(data.pyvider_env_variables.app_common.sensitive_values)
    }

    environment_config = {
      database_configured = local.env_config.database_url != ""
      redis_configured = local.env_config.redis_url != ""
      api_configured = local.env_config.api_base_url != ""
      debug_enabled = local.env_config.debug_enabled
      log_level = local.env_config.log_level
    }

    feature_flags_enabled = [
      for flag, enabled in local.feature_flags : flag if enabled
    ]

    validation = {
      passed = length(local.validation_errors) == 0
      error_count = length(local.validation_errors)
      # Don't expose actual errors in output for security
    }

    generated_files = [
      pyvider_file_content.app_config.filename,
      pyvider_file_content.docker_env.filename,
      pyvider_file_content.environment_comparison.filename,
      pyvider_file_content.validation_report.filename
    ]

    system_info = local.system_info
  }
}