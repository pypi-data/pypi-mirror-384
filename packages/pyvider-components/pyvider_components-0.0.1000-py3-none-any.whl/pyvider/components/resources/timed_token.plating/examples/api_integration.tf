# API integration token examples

# Example 1: External API authentication
resource "pyvider_timed_token" "external_api" {
  name = "external-service-integration"
}

# Use token for API authentication
data "pyvider_http_api" "authenticated_request" {
  url = "https://api.example.com/v1/data"
  headers = {
    "Authorization" = "Bearer ${pyvider_timed_token.external_api.token}"
    "Content-Type"  = "application/json"
    "X-API-Version" = "2024-01-01"
    "X-Token-ID"    = pyvider_timed_token.external_api.id
  }
}

# Example 2: Webhook authentication token
resource "pyvider_timed_token" "webhook_auth" {
  name = "webhook-callback-auth"
}

# Configure webhook with temporary authentication
data "pyvider_http_api" "register_webhook" {
  url    = "https://webhooks.example.com/register"
  method = "POST"
  headers = {
    "Authorization" = "Bearer ${pyvider_timed_token.webhook_auth.token}"
    "Content-Type"  = "application/json"
  }
}

# Create webhook configuration file
resource "pyvider_file_content" "webhook_config" {
  filename = "/tmp/webhook_config.json"
  content = jsonencode({
    webhook = {
      endpoint = "https://our-service.example.com/webhook"
      authentication = {
        type = "bearer_token"
        token_id = pyvider_timed_token.webhook_auth.id
        token_name = pyvider_timed_token.webhook_auth.name
        expires_at = pyvider_timed_token.webhook_auth.expires_at
      }
      events = ["user.created", "user.updated", "user.deleted"]
      retry_policy = {
        max_attempts = 3
        backoff_seconds = [1, 5, 15]
      }
    }
    security = {
      verify_signature = true
      allowed_ips = ["192.168.1.0/24", "10.0.0.0/8"]
      rate_limit = {
        requests_per_minute = 100
        burst_limit = 10
      }
    }
  })
}

# Example 3: Database API token
resource "pyvider_timed_token" "database_api" {
  name = "database-service-token"
}

# Create database connection configuration
resource "pyvider_file_content" "database_api_config" {
  filename = "/tmp/database_api_config.json"
  content = jsonencode({
    database_api = {
      connection = {
        base_url = "https://db-api.example.com/v2"
        authentication = {
          method = "api_token"
          token_id = pyvider_timed_token.database_api.id
          token_name = pyvider_timed_token.database_api.name
          expires_at = pyvider_timed_token.database_api.expires_at
        }
        timeout_seconds = 30
        retry_attempts = 3
      }
      endpoints = {
        query = "/query"
        batch = "/batch"
        schema = "/schema"
        health = "/health"
      }
      permissions = {
        read = true
        write = false
        admin = false
      }
    }
    connection_pool = {
      max_connections = 10
      idle_timeout_seconds = 300
      connection_lifetime_hours = 1
    }
  })
}

# Example 4: Multi-service API orchestration
resource "pyvider_timed_token" "service_orchestrator" {
  name = "service-orchestration-token"
}

resource "pyvider_timed_token" "payment_service" {
  name = "payment-service-token"
}

resource "pyvider_timed_token" "notification_service" {
  name = "notification-service-token"
}

# Create service orchestration configuration
resource "pyvider_file_content" "service_orchestration" {
  filename = "/tmp/service_orchestration.json"
  content = jsonencode({
    orchestration = {
      coordinator = {
        token_id = pyvider_timed_token.service_orchestrator.id
        token_name = pyvider_timed_token.service_orchestrator.name
        expires_at = pyvider_timed_token.service_orchestrator.expires_at
      }

      services = {
        payment = {
          base_url = "https://payments.example.com/api/v1"
          token_id = pyvider_timed_token.payment_service.id
          token_name = pyvider_timed_token.payment_service.name
          expires_at = pyvider_timed_token.payment_service.expires_at
          timeout_seconds = 15
          retry_policy = "exponential_backoff"
        }

        notifications = {
          base_url = "https://notify.example.com/api/v1"
          token_id = pyvider_timed_token.notification_service.id
          token_name = pyvider_timed_token.notification_service.name
          expires_at = pyvider_timed_token.notification_service.expires_at
          timeout_seconds = 10
          retry_policy = "immediate_retry"
        }
      }

      workflows = {
        user_registration = {
          steps = [
            {
              service = "payment"
              endpoint = "/customers"
              method = "POST"
              timeout = 15
            },
            {
              service = "notifications"
              endpoint = "/welcome"
              method = "POST"
              timeout = 5
            }
          ]
          rollback_enabled = true
          max_duration_seconds = 60
        }
      }
    }

    monitoring = {
      health_checks = {
        enabled = true
        interval_seconds = 30
        failure_threshold = 3
      }
      token_expiration = {
        warn_before_minutes = 10
        auto_refresh = false
      }
    }
  })
}

# Example 5: GraphQL API integration
resource "pyvider_timed_token" "graphql_api" {
  name = "graphql-service-token"
}

# Create GraphQL client configuration
resource "pyvider_file_content" "graphql_config" {
  filename = "/tmp/graphql_config.json"
  content = jsonencode({
    graphql_client = {
      endpoint = "https://graphql.example.com/api"
      authentication = {
        type = "bearer_token"
        token_id = pyvider_timed_token.graphql_api.id
        token_name = pyvider_timed_token.graphql_api.name
        expires_at = pyvider_timed_token.graphql_api.expires_at
        header_name = "Authorization"
        header_format = "Bearer {token}"
      }

      introspection = {
        enabled = true
        cache_schema = true
        schema_ttl_minutes = 30
      }

      queries = {
        user_profile = {
          query = "query GetUser($id: ID!) { user(id: $id) { id name email profile { avatar bio } } }"
          variables = {
            id = "$USER_ID"
          }
        }
        user_posts = {
          query = "query GetUserPosts($userId: ID!, $limit: Int) { posts(userId: $userId, limit: $limit) { id title content createdAt } }"
          variables = {
            userId = "$USER_ID"
            limit = 10
          }
        }
      }

      mutations = {
        create_post = {
          mutation = "mutation CreatePost($input: PostInput!) { createPost(input: $input) { id title content author { name } } }"
          variables = {
            input = "$POST_INPUT"
          }
        }
      }

      subscriptions = {
        post_updates = {
          subscription = "subscription PostUpdates($userId: ID!) { postUpdated(userId: $userId) { id title content updatedAt } }"
          variables = {
            userId = "$USER_ID"
          }
        }
      }
    }

    client_options = {
      timeout_seconds = 30
      retry_attempts = 3
      batch_requests = true
      persistent_queries = false
    }
  })
}

# Example 6: Token rotation strategy for long-running integrations
resource "pyvider_timed_token" "primary_integration" {
  name = "primary-api-integration"
}

resource "pyvider_timed_token" "backup_integration" {
  name = "backup-api-integration"
}

# Create token rotation configuration
resource "pyvider_file_content" "token_rotation_strategy" {
  filename = "/tmp/token_rotation_strategy.json"
  content = jsonencode({
    token_rotation = {
      strategy = "blue_green"

      primary_token = {
        token_id = pyvider_timed_token.primary_integration.id
        token_name = pyvider_timed_token.primary_integration.name
        expires_at = pyvider_timed_token.primary_integration.expires_at
        status = "active"
        priority = 1
      }

      backup_token = {
        token_id = pyvider_timed_token.backup_integration.id
        token_name = pyvider_timed_token.backup_integration.name
        expires_at = pyvider_timed_token.backup_integration.expires_at
        status = "standby"
        priority = 2
      }

      rotation_policy = {
        trigger_before_expiry_minutes = 15
        overlap_period_minutes = 5
        validation_checks = [
          "token_format",
          "api_connectivity",
          "permission_validation"
        ]
        fallback_enabled = true
        notification_channels = ["email", "slack", "webhook"]
      }

      monitoring = {
        health_endpoint = "/health/tokens"
        check_interval_seconds = 60
        alert_on_failure = true
        metrics = {
          token_usage_rate = true
          api_response_times = true
          error_rates = true
          expiration_warnings = true
        }
      }
    }

    failover = {
      automatic = true
      max_retry_attempts = 3
      circuit_breaker = {
        failure_threshold = 5
        reset_timeout_seconds = 300
      }
    }
  })
}

# Create comprehensive API integration summary
resource "pyvider_file_content" "api_integration_summary" {
  filename = "/tmp/api_integration_summary.txt"
  content = join("\n", [
    "=== API Integration Token Summary ===",
    "",
    "External API Integration:",
    "  Token: ${pyvider_timed_token.external_api.name}",
    "  ID: ${pyvider_timed_token.external_api.id}",
    "  Expires: ${pyvider_timed_token.external_api.expires_at}",
    "  API Status: ${data.pyvider_http_api.authenticated_request.status_code}",
    "",
    "Webhook Authentication:",
    "  Token: ${pyvider_timed_token.webhook_auth.name}",
    "  ID: ${pyvider_timed_token.webhook_auth.id}",
    "  Expires: ${pyvider_timed_token.webhook_auth.expires_at}",
    "  Registration Status: ${data.pyvider_http_api.register_webhook.status_code}",
    "",
    "Database API Integration:",
    "  Token: ${pyvider_timed_token.database_api.name}",
    "  ID: ${pyvider_timed_token.database_api.id}",
    "  Expires: ${pyvider_timed_token.database_api.expires_at}",
    "",
    "Service Orchestration:",
    "  Coordinator: ${pyvider_timed_token.service_orchestrator.name}",
    "  Payment Service: ${pyvider_timed_token.payment_service.name}",
    "  Notification Service: ${pyvider_timed_token.notification_service.name}",
    "",
    "GraphQL Integration:",
    "  Token: ${pyvider_timed_token.graphql_api.name}",
    "  ID: ${pyvider_timed_token.graphql_api.id}",
    "  Expires: ${pyvider_timed_token.graphql_api.expires_at}",
    "",
    "Token Rotation Strategy:",
    "  Primary: ${pyvider_timed_token.primary_integration.name}",
    "  Backup: ${pyvider_timed_token.backup_integration.name}",
    "",
    "Security Features:",
    "  ✅ Time-limited tokens (1 hour expiration)",
    "  ✅ Sensitive data protection",
    "  ✅ Automatic token rotation support",
    "  ✅ Multi-service orchestration",
    "  ✅ Fallback and redundancy",
    "",
    "Integration Patterns Demonstrated:",
    "  - REST API authentication",
    "  - Webhook registration and callbacks",
    "  - Database service integration",
    "  - Multi-service orchestration",
    "  - GraphQL API integration",
    "  - Token rotation strategies",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "api_integration_results" {
  description = "API integration token configurations and results"
  value = {
    integrations = {
      external_api = {
        token_name = pyvider_timed_token.external_api.name
        token_id = pyvider_timed_token.external_api.id
        expires_at = pyvider_timed_token.external_api.expires_at
        api_status = data.pyvider_http_api.authenticated_request.status_code
        api_success = data.pyvider_http_api.authenticated_request.status_code >= 200 && data.pyvider_http_api.authenticated_request.status_code < 300
      }

      webhook = {
        token_name = pyvider_timed_token.webhook_auth.name
        token_id = pyvider_timed_token.webhook_auth.id
        expires_at = pyvider_timed_token.webhook_auth.expires_at
        registration_status = data.pyvider_http_api.register_webhook.status_code
        registration_success = data.pyvider_http_api.register_webhook.status_code >= 200 && data.pyvider_http_api.register_webhook.status_code < 300
      }

      database_api = {
        token_name = pyvider_timed_token.database_api.name
        token_id = pyvider_timed_token.database_api.id
        expires_at = pyvider_timed_token.database_api.expires_at
      }

      graphql = {
        token_name = pyvider_timed_token.graphql_api.name
        token_id = pyvider_timed_token.graphql_api.id
        expires_at = pyvider_timed_token.graphql_api.expires_at
      }
    }

    service_orchestration = {
      coordinator = pyvider_timed_token.service_orchestrator.name
      payment_service = pyvider_timed_token.payment_service.name
      notification_service = pyvider_timed_token.notification_service.name
      all_services_configured = true
    }

    token_rotation = {
      primary_token = pyvider_timed_token.primary_integration.name
      backup_token = pyvider_timed_token.backup_integration.name
      strategy = "blue_green"
      redundancy_enabled = true
    }

    summary = {
      total_tokens = 8
      integration_types = ["REST API", "Webhook", "Database API", "GraphQL", "Service Orchestration"]
      security_features = ["Time-limited", "Sensitive data protection", "Token rotation", "Failover support"]
    }

    configuration_files = [
      pyvider_file_content.webhook_config.filename,
      pyvider_file_content.database_api_config.filename,
      pyvider_file_content.service_orchestration.filename,
      pyvider_file_content.graphql_config.filename,
      pyvider_file_content.token_rotation_strategy.filename,
      pyvider_file_content.api_integration_summary.filename
    ]
  }
}