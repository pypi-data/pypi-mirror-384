# Environment-specific configuration management

# Define environment variables
variable "environment" {
  description = "The deployment environment"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

# Environment-specific database configuration
locals {
  database_configs = {
    development = {
      host     = "localhost"
      port     = 5432
      database = "myapp_dev"
      pool_size = 5
    }
    staging = {
      host     = "staging-db.example.com"
      port     = 5432
      database = "myapp_staging"
      pool_size = 10
    }
    production = {
      host     = "prod-db.example.com"
      port     = 5432
      database = "myapp_prod"
      pool_size = 20
    }
  }

  # Get configuration for current environment
  db_config = local.database_configs[var.environment]

  # Environment-specific feature flags
  feature_flags = {
    development = {
      debug_mode    = true
      verbose_logs  = true
      dev_tools     = true
      metrics       = false
    }
    staging = {
      debug_mode    = false
      verbose_logs  = true
      dev_tools     = false
      metrics       = true
    }
    production = {
      debug_mode    = false
      verbose_logs  = false
      dev_tools     = false
      metrics       = true
    }
  }
}

# Create environment-specific application configuration
resource "pyvider_file_content" "app_config_env" {
  filename = "/tmp/config-${var.environment}.properties"
  content = join("\n", [
    "# Application Configuration for ${upper(var.environment)}",
    "# Generated on ${timestamp()}",
    "",
    "# Application Settings",
    "app.name=my-terraform-app",
    "app.version=${var.app_version}",
    "app.environment=${var.environment}",
    "",
    "# Database Configuration",
    "database.host=${local.db_config.host}",
    "database.port=${local.db_config.port}",
    "database.name=${local.db_config.database}",
    "database.pool.size=${local.db_config.pool_size}",
    "",
    "# Feature Flags",
    "features.debug=${local.feature_flags[var.environment].debug_mode}",
    "features.verbose_logs=${local.feature_flags[var.environment].verbose_logs}",
    "features.dev_tools=${local.feature_flags[var.environment].dev_tools}",
    "features.metrics=${local.feature_flags[var.environment].metrics}",
    "",
    "# Security Settings",
    "security.jwt.expiry=${var.environment == "production" ? "15m" : "24h"}",
    "security.cors.enabled=${var.environment != "production"}",
    "security.ssl.required=${var.environment == "production"}"
  ])
}

# Create environment-specific Docker environment file
resource "pyvider_file_content" "docker_env" {
  filename = "/tmp/.env.${var.environment}"
  content = join("\n", [
    "# Docker Environment Variables for ${upper(var.environment)}",
    "",
    "# Application",
    "APP_ENV=${var.environment}",
    "APP_VERSION=${var.app_version}",
    "APP_DEBUG=${local.feature_flags[var.environment].debug_mode}",
    "",
    "# Database",
    "DATABASE_HOST=${local.db_config.host}",
    "DATABASE_PORT=${local.db_config.port}",
    "DATABASE_NAME=${local.db_config.database}",
    "DATABASE_POOL_SIZE=${local.db_config.pool_size}",
    "",
    "# Logging",
    "LOG_LEVEL=${local.feature_flags[var.environment].verbose_logs ? "DEBUG" : "INFO"}",
    "",
    "# Performance",
    "WORKER_PROCESSES=${var.environment == "production" ? "4" : "2"}",
    "CACHE_TTL=${var.environment == "production" ? "3600" : "60"}",
    "",
    "# Monitoring",
    "METRICS_ENABLED=${local.feature_flags[var.environment].metrics}",
    "HEALTH_CHECK_INTERVAL=${var.environment == "production" ? "30" : "60"}"
  ])
}

# Create a conditional configuration file (only for non-production)
resource "pyvider_file_content" "dev_config" {
  count = var.environment != "production" ? 1 : 0

  filename = "/tmp/development-tools.conf"
  content = <<-EOF
    # Development Tools Configuration
    # This file only exists in non-production environments

    [hot_reload]
    enabled = true
    watch_patterns = ["*.py", "*.js", "*.css"]
    ignore_patterns = ["*.pyc", "node_modules/"]

    [debug_toolbar]
    enabled = true
    profiling = true
    sql_debug = true

    [test_data]
    seed_database = true
    create_test_users = true
    mock_external_apis = true

    [development_server]
    auto_restart = true
    debug_mode = true
    verbose_errors = true
  EOF
}

output "environment_configs" {
  description = "Information about environment-specific configuration files"
  value = {
    environment = var.environment
    app_config = {
      path         = pyvider_file_content.app_config_env.filename
      content_hash = pyvider_file_content.app_config_env.content_hash
    }
    docker_env = {
      path         = pyvider_file_content.docker_env.filename
      content_hash = pyvider_file_content.docker_env.content_hash
    }
    dev_config_created = var.environment != "production"
    dev_config = var.environment != "production" ? {
      path         = pyvider_file_content.dev_config[0].filename
      content_hash = pyvider_file_content.dev_config[0].content_hash
    } : null
  }
}