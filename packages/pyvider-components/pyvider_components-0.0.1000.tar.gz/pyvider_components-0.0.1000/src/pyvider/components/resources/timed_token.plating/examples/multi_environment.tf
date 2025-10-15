# Multi-environment token management examples

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "application_name" {
  description = "Name of the application"
  type        = string
  default     = "example-app"
}

# Environment-specific token configuration
locals {
  env_config = {
    development = {
      token_prefix = "dev"
      monitoring_level = "basic"
      rotation_required = false
      alert_channels = ["email"]
      backup_tokens = 1
    }
    staging = {
      token_prefix = "staging"
      monitoring_level = "enhanced"
      rotation_required = true
      alert_channels = ["email", "slack"]
      backup_tokens = 2
    }
    production = {
      token_prefix = "prod"
      monitoring_level = "comprehensive"
      rotation_required = true
      alert_channels = ["email", "slack", "pagerduty"]
      backup_tokens = 3
    }
  }

  current_config = local.env_config[var.environment]
}

# Example 1: Environment-specific application tokens
resource "pyvider_timed_token" "app_primary" {
  name = "${local.current_config.token_prefix}-${var.application_name}-primary"
}

resource "pyvider_timed_token" "app_backup" {
  count = local.current_config.backup_tokens
  name  = "${local.current_config.token_prefix}-${var.application_name}-backup-${count.index + 1}"
}

# Example 2: Database tokens per environment
resource "pyvider_timed_token" "database_read" {
  name = "${local.current_config.token_prefix}-database-readonly"
}

resource "pyvider_timed_token" "database_write" {
  count = var.environment == "production" ? 1 : 0
  name  = "${local.current_config.token_prefix}-database-readwrite"
}

# Example 3: API gateway tokens
resource "pyvider_timed_token" "api_gateway" {
  name = "${local.current_config.token_prefix}-api-gateway"
}

resource "pyvider_timed_token" "api_internal" {
  name = "${local.current_config.token_prefix}-internal-services"
}

# Example 4: Monitoring and observability tokens
resource "pyvider_timed_token" "metrics_collector" {
  name = "${local.current_config.token_prefix}-metrics-collector"
}

resource "pyvider_timed_token" "log_aggregator" {
  name = "${local.current_config.token_prefix}-log-aggregator"
}

resource "pyvider_timed_token" "trace_collector" {
  count = var.environment != "development" ? 1 : 0
  name  = "${local.current_config.token_prefix}-trace-collector"
}

# Create environment-specific token registry
resource "pyvider_file_content" "token_registry" {
  filename = "/tmp/${var.environment}_token_registry.json"
  content = jsonencode({
    environment = var.environment
    application = var.application_name
    timestamp = timestamp()

    configuration = local.current_config

    tokens = {
      application = {
        primary = {
          name = pyvider_timed_token.app_primary.name
          id = pyvider_timed_token.app_primary.id
          expires_at = pyvider_timed_token.app_primary.expires_at
          type = "primary"
        }
        backups = [
          for i, token in pyvider_timed_token.app_backup : {
            name = token.name
            id = token.id
            expires_at = token.expires_at
            type = "backup"
            sequence = i + 1
          }
        ]
      }

      database = {
        readonly = {
          name = pyvider_timed_token.database_read.name
          id = pyvider_timed_token.database_read.id
          expires_at = pyvider_timed_token.database_read.expires_at
          permissions = ["read", "list"]
        }
        readwrite = var.environment == "production" ? {
          name = pyvider_timed_token.database_write[0].name
          id = pyvider_timed_token.database_write[0].id
          expires_at = pyvider_timed_token.database_write[0].expires_at
          permissions = ["read", "write", "list", "delete"]
        } : null
      }

      api_services = {
        gateway = {
          name = pyvider_timed_token.api_gateway.name
          id = pyvider_timed_token.api_gateway.id
          expires_at = pyvider_timed_token.api_gateway.expires_at
          scope = "external"
        }
        internal = {
          name = pyvider_timed_token.api_internal.name
          id = pyvider_timed_token.api_internal.id
          expires_at = pyvider_timed_token.api_internal.expires_at
          scope = "internal"
        }
      }

      observability = {
        metrics = {
          name = pyvider_timed_token.metrics_collector.name
          id = pyvider_timed_token.metrics_collector.id
          expires_at = pyvider_timed_token.metrics_collector.expires_at
          service = "prometheus"
        }
        logs = {
          name = pyvider_timed_token.log_aggregator.name
          id = pyvider_timed_token.log_aggregator.id
          expires_at = pyvider_timed_token.log_aggregator.expires_at
          service = "elasticsearch"
        }
        traces = var.environment != "development" ? {
          name = pyvider_timed_token.trace_collector[0].name
          id = pyvider_timed_token.trace_collector[0].id
          expires_at = pyvider_timed_token.trace_collector[0].expires_at
          service = "jaeger"
        } : null
      }
    }

    security_policy = {
      rotation_required = local.current_config.rotation_required
      monitoring_level = local.current_config.monitoring_level
      backup_strategy = "multiple_tokens"
      alert_channels = local.current_config.alert_channels
    }

    compliance = {
      environment_isolation = true
      token_segregation = true
      principle_of_least_privilege = true
      automatic_expiration = true
    }
  })
}

# Create environment-specific application configuration
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/${var.environment}_app_config.yaml"
  content = yamlencode({
    application = {
      name = var.application_name
      environment = var.environment

      authentication = {
        primary_token = {
          id = pyvider_timed_token.app_primary.id
          name = pyvider_timed_token.app_primary.name
          expires_at = pyvider_timed_token.app_primary.expires_at
        }

        backup_tokens = [
          for token in pyvider_timed_token.app_backup : {
            id = token.id
            name = token.name
            expires_at = token.expires_at
          }
        ]

        rotation_policy = {
          enabled = local.current_config.rotation_required
          warn_before_minutes = var.environment == "production" ? 10 : 30
          fallback_enabled = length(pyvider_timed_token.app_backup) > 0
        }
      }

      database = {
        connections = {
          readonly = {
            token_id = pyvider_timed_token.database_read.id
            token_name = pyvider_timed_token.database_read.name
            expires_at = pyvider_timed_token.database_read.expires_at
            max_connections = var.environment == "production" ? 20 : 5
          }
          readwrite = var.environment == "production" ? {
            token_id = pyvider_timed_token.database_write[0].id
            token_name = pyvider_timed_token.database_write[0].name
            expires_at = pyvider_timed_token.database_write[0].expires_at
            max_connections = 10
          } : null
        }
      }

      apis = {
        gateway = {
          token_id = pyvider_timed_token.api_gateway.id
          token_name = pyvider_timed_token.api_gateway.name
          expires_at = pyvider_timed_token.api_gateway.expires_at
          base_url = "https://${var.environment == "production" ? "api" : "${var.environment}-api"}.example.com"
          timeout_seconds = var.environment == "production" ? 10 : 30
        }
        internal = {
          token_id = pyvider_timed_token.api_internal.id
          token_name = pyvider_timed_token.api_internal.name
          expires_at = pyvider_timed_token.api_internal.expires_at
          base_url = "https://internal-${var.environment}.example.com"
          timeout_seconds = 15
        }
      }

      observability = {
        metrics = {
          enabled = true
          token_id = pyvider_timed_token.metrics_collector.id
          token_name = pyvider_timed_token.metrics_collector.name
          expires_at = pyvider_timed_token.metrics_collector.expires_at
          endpoint = "https://metrics-${var.environment}.example.com"
          interval_seconds = var.environment == "production" ? 15 : 60
        }

        logging = {
          enabled = true
          token_id = pyvider_timed_token.log_aggregator.id
          token_name = pyvider_timed_token.log_aggregator.name
          expires_at = pyvider_timed_token.log_aggregator.expires_at
          endpoint = "https://logs-${var.environment}.example.com"
          level = var.environment == "production" ? "warn" : (var.environment == "staging" ? "info" : "debug")
        }

        tracing = var.environment != "development" ? {
          enabled = true
          token_id = pyvider_timed_token.trace_collector[0].id
          token_name = pyvider_timed_token.trace_collector[0].name
          expires_at = pyvider_timed_token.trace_collector[0].expires_at
          endpoint = "https://traces-${var.environment}.example.com"
          sampling_rate = var.environment == "production" ? 0.1 : 1.0
        } : {
          enabled = false
        }
      }
    }

    environment_metadata = {
      deployment_tier = var.environment
      monitoring_level = local.current_config.monitoring_level
      compliance_required = var.environment == "production"
      backup_tokens_count = local.current_config.backup_tokens
    }
  })
}

# Create monitoring configuration
resource "pyvider_file_content" "monitoring_config" {
  filename = "/tmp/${var.environment}_monitoring.json"
  content = jsonencode({
    monitoring = {
      environment = var.environment
      application = var.application_name
      level = local.current_config.monitoring_level

      token_monitoring = {
        primary_application = {
          token_id = pyvider_timed_token.app_primary.id
          token_name = pyvider_timed_token.app_primary.name
          expires_at = pyvider_timed_token.app_primary.expires_at
          criticality = "high"
          alert_thresholds = {
            expiry_warning_minutes = var.environment == "production" ? 10 : 30
            usage_anomaly_threshold = 2.0
          }
        }

        backup_tokens = [
          for i, token in pyvider_timed_token.app_backup : {
            token_id = token.id
            token_name = token.name
            expires_at = token.expires_at
            criticality = "medium"
            sequence = i + 1
          }
        ]

        infrastructure_tokens = [
          {
            service = "database_readonly"
            token_id = pyvider_timed_token.database_read.id
            token_name = pyvider_timed_token.database_read.name
            expires_at = pyvider_timed_token.database_read.expires_at
            criticality = "high"
          },
          {
            service = "api_gateway"
            token_id = pyvider_timed_token.api_gateway.id
            token_name = pyvider_timed_token.api_gateway.name
            expires_at = pyvider_timed_token.api_gateway.expires_at
            criticality = "high"
          },
          {
            service = "internal_apis"
            token_id = pyvider_timed_token.api_internal.id
            token_name = pyvider_timed_token.api_internal.name
            expires_at = pyvider_timed_token.api_internal.expires_at
            criticality = "medium"
          }
        ]

        observability_tokens = [
          {
            service = "metrics_collection"
            token_id = pyvider_timed_token.metrics_collector.id
            token_name = pyvider_timed_token.metrics_collector.name
            expires_at = pyvider_timed_token.metrics_collector.expires_at
            criticality = "medium"
          },
          {
            service = "log_aggregation"
            token_id = pyvider_timed_token.log_aggregator.id
            token_name = pyvider_timed_token.log_aggregator.name
            expires_at = pyvider_timed_token.log_aggregator.expires_at
            criticality = "medium"
          }
        ]
      }

      alert_configuration = {
        channels = local.current_config.alert_channels
        escalation_policy = {
          immediate = var.environment == "production"
          business_hours_only = var.environment == "development"
          weekend_alerts = var.environment != "development"
        }
        notification_templates = {
          token_expiry = "Token ${var.token_name} (${var.token_id}) expires at ${var.expires_at}"
          token_rotation = "Token rotation required for ${var.environment} environment"
          token_failure = "Token authentication failed for service ${var.service_name}"
        }
      }

      health_checks = {
        enabled = true
        interval_seconds = var.environment == "production" ? 30 : 300
        timeout_seconds = 10
        failure_threshold = var.environment == "production" ? 2 : 5

        endpoints = [
          {
            name = "token_validation"
            url = "https://auth-${var.environment}.example.com/validate"
            method = "POST"
            expected_status = 200
          },
          {
            name = "api_gateway_health"
            url = "https://${var.environment == "production" ? "api" : "${var.environment}-api"}.example.com/health"
            method = "GET"
            expected_status = 200
          }
        ]
      }
    }

    compliance = {
      audit_logging = var.environment == "production"
      token_lifecycle_tracking = true
      access_review_required = var.environment == "production"
      encryption_at_rest = true
      encryption_in_transit = true
    }
  })
}

# Create deployment summary
resource "pyvider_file_content" "deployment_summary" {
  filename = "/tmp/${var.environment}_deployment_summary.txt"
  content = join("\n", [
    "=== ${title(var.environment)} Environment Token Deployment ===",
    "",
    "Application: ${var.application_name}",
    "Environment: ${var.environment}",
    "Configuration Level: ${local.current_config.monitoring_level}",
    "Generated: ${timestamp()}",
    "",
    "=== Application Tokens ===",
    "Primary Token:",
    "  Name: ${pyvider_timed_token.app_primary.name}",
    "  ID: ${pyvider_timed_token.app_primary.id}",
    "  Expires: ${pyvider_timed_token.app_primary.expires_at}",
    "",
    "Backup Tokens (${length(pyvider_timed_token.app_backup)}):",
    join("\n", [
      for i, token in pyvider_timed_token.app_backup :
      "  ${i + 1}. ${token.name} (${token.id}) - Expires: ${token.expires_at}"
    ]),
    "",
    "=== Infrastructure Tokens ===",
    "Database Access:",
    "  Read-Only: ${pyvider_timed_token.database_read.name} (${pyvider_timed_token.database_read.id})",
    var.environment == "production" ? "  Read-Write: ${pyvider_timed_token.database_write[0].name} (${pyvider_timed_token.database_write[0].id})" : "  Read-Write: Not configured for ${var.environment}",
    "",
    "API Services:",
    "  Gateway: ${pyvider_timed_token.api_gateway.name} (${pyvider_timed_token.api_gateway.id})",
    "  Internal: ${pyvider_timed_token.api_internal.name} (${pyvider_timed_token.api_internal.id})",
    "",
    "=== Observability Tokens ===",
    "Metrics: ${pyvider_timed_token.metrics_collector.name} (${pyvider_timed_token.metrics_collector.id})",
    "Logs: ${pyvider_timed_token.log_aggregator.name} (${pyvider_timed_token.log_aggregator.id})",
    var.environment != "development" ? "Traces: ${pyvider_timed_token.trace_collector[0].name} (${pyvider_timed_token.trace_collector[0].id})" : "Traces: Disabled for development",
    "",
    "=== Security Configuration ===",
    "Token Rotation Required: ${local.current_config.rotation_required ? "Yes" : "No"}",
    "Monitoring Level: ${title(local.current_config.monitoring_level)}",
    "Alert Channels: ${join(", ", local.current_config.alert_channels)}",
    "Backup Tokens: ${local.current_config.backup_tokens}",
    "",
    "=== Compliance Features ===",
    "✅ Environment Isolation",
    "✅ Automatic Token Expiration",
    "✅ Sensitive Data Protection",
    "✅ Token Lifecycle Management",
    var.environment == "production" ? "✅ Production Security Controls" : "ℹ️  Development Environment (Relaxed Controls)",
    "",
    "⚠️  All tokens are time-limited and will expire in 1 hour.",
    "⚠️  Monitor expiration times and plan for rotation.",
    var.environment == "production" ? "⚠️  Production environment requires immediate attention for token issues." : "",
    "",
    "Configuration files generated:",
    "- ${pyvider_file_content.token_registry.filename}",
    "- ${pyvider_file_content.app_config.filename}",
    "- ${pyvider_file_content.monitoring_config.filename}",
    "- ${pyvider_file_content.deployment_summary.filename}"
  ])
}

output "multi_environment_deployment" {
  description = "Multi-environment token deployment summary"
  value = {
    environment = var.environment
    application = var.application_name
    configuration = local.current_config

    tokens = {
      application = {
        primary = {
          name = pyvider_timed_token.app_primary.name
          id = pyvider_timed_token.app_primary.id
          expires_at = pyvider_timed_token.app_primary.expires_at
        }
        backup_count = length(pyvider_timed_token.app_backup)
      }

      infrastructure = {
        database_readonly = {
          name = pyvider_timed_token.database_read.name
          id = pyvider_timed_token.database_read.id
        }
        database_readwrite_enabled = var.environment == "production"
        api_gateway = {
          name = pyvider_timed_token.api_gateway.name
          id = pyvider_timed_token.api_gateway.id
        }
        internal_apis = {
          name = pyvider_timed_token.api_internal.name
          id = pyvider_timed_token.api_internal.id
        }
      }

      observability = {
        metrics_enabled = true
        logging_enabled = true
        tracing_enabled = var.environment != "development"
      }
    }

    security = {
      rotation_required = local.current_config.rotation_required
      monitoring_level = local.current_config.monitoring_level
      backup_strategy = local.current_config.backup_tokens > 0
      alert_channels = local.current_config.alert_channels
    }

    files_generated = [
      pyvider_file_content.token_registry.filename,
      pyvider_file_content.app_config.filename,
      pyvider_file_content.monitoring_config.filename,
      pyvider_file_content.deployment_summary.filename
    ]

    total_tokens = (
      1 + # primary
      length(pyvider_timed_token.app_backup) + # backups
      1 + # database read
      (var.environment == "production" ? 1 : 0) + # database write
      2 + # api tokens
      2 + # observability (metrics + logs)
      (var.environment != "development" ? 1 : 0) # tracing
    )
  }
}