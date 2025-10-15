# Basic timed token examples

# Example 1: Simple token generation
resource "pyvider_timed_token" "simple" {
  name = "basic-example-token"
}

# Example 2: Token for API integration
resource "pyvider_timed_token" "api_auth" {
  name = "api-integration-token"
}

# Create configuration file with token
resource "pyvider_file_content" "api_config" {
  filename = "/tmp/api_config.json"
  content = jsonencode({
    authentication = {
      token_id = pyvider_timed_token.api_auth.id
      token_name = pyvider_timed_token.api_auth.name
      expires_at = pyvider_timed_token.api_auth.expires_at
      # Note: token value is sensitive and not included in config file
      token_available = pyvider_timed_token.api_auth.token != null
    }
    api_endpoint = "https://api.example.com/v1"
    timeout_seconds = 30
    retry_attempts = 3
  })
}

# Example 3: Token for service authentication
resource "pyvider_timed_token" "service_auth" {
  name = "background-service-token"
}

# Create service configuration
resource "pyvider_file_content" "service_config" {
  filename = "/tmp/service_config.yaml"
  content = yamlencode({
    service = {
      name = "background-processor"
      authentication = {
        method = "bearer_token"
        token_name = pyvider_timed_token.service_auth.name
        token_id = pyvider_timed_token.service_auth.id
        expires_at = pyvider_timed_token.service_auth.expires_at
      }
      endpoints = {
        health_check = "/health"
        metrics = "/metrics"
        ready = "/ready"
      }
    }
  })
}

# Example 4: Multiple tokens for different purposes
resource "pyvider_timed_token" "read_token" {
  name = "readonly-access-token"
}

resource "pyvider_timed_token" "write_token" {
  name = "write-access-token"
}

# Create access control configuration
resource "pyvider_file_content" "access_control" {
  filename = "/tmp/access_control.json"
  content = jsonencode({
    access_tokens = {
      readonly = {
        token_id = pyvider_timed_token.read_token.id
        name = pyvider_timed_token.read_token.name
        expires_at = pyvider_timed_token.read_token.expires_at
        permissions = ["read", "list"]
        scope = "user_data"
      }
      readwrite = {
        token_id = pyvider_timed_token.write_token.id
        name = pyvider_timed_token.write_token.name
        expires_at = pyvider_timed_token.write_token.expires_at
        permissions = ["read", "write", "delete", "list"]
        scope = "user_data"
      }
    }
    token_validation = {
      check_expiration = true
      require_https = true
      audience = "api.example.com"
    }
  })
}

# Example 5: Token with monitoring configuration
resource "pyvider_timed_token" "monitored_token" {
  name = "production-api-token"
}

# Create monitoring and alerting configuration
resource "pyvider_file_content" "token_monitoring" {
  filename = "/tmp/token_monitoring.json"
  content = jsonencode({
    token_monitoring = {
      token_id = pyvider_timed_token.monitored_token.id
      token_name = pyvider_timed_token.monitored_token.name
      expires_at = pyvider_timed_token.monitored_token.expires_at

      alerts = {
        expiration_warning = {
          enabled = true
          warn_before_minutes = 15
          notification_channels = ["email", "slack"]
        }
        usage_monitoring = {
          enabled = true
          track_requests = true
          alert_on_unusual_activity = true
        }
      }

      rotation_policy = {
        automatic = false
        manual_approval_required = true
        advance_notice_hours = 4
      }
    }

    metadata = {
      environment = "production"
      service = "api-gateway"
      owner = "platform-team"
      created_at = timestamp()
    }
  })
}

# Create token registry for tracking
resource "pyvider_file_content" "token_registry" {
  filename = "/tmp/token_registry.txt"
  content = join("\n", [
    "=== Token Registry ===",
    "",
    "Basic Token:",
    "  Name: ${pyvider_timed_token.simple.name}",
    "  ID: ${pyvider_timed_token.simple.id}",
    "  Expires: ${pyvider_timed_token.simple.expires_at}",
    "",
    "API Authentication Token:",
    "  Name: ${pyvider_timed_token.api_auth.name}",
    "  ID: ${pyvider_timed_token.api_auth.id}",
    "  Expires: ${pyvider_timed_token.api_auth.expires_at}",
    "",
    "Service Authentication Token:",
    "  Name: ${pyvider_timed_token.service_auth.name}",
    "  ID: ${pyvider_timed_token.service_auth.id}",
    "  Expires: ${pyvider_timed_token.service_auth.expires_at}",
    "",
    "Access Control Tokens:",
    "  Read Token: ${pyvider_timed_token.read_token.name} (${pyvider_timed_token.read_token.id})",
    "  Write Token: ${pyvider_timed_token.write_token.name} (${pyvider_timed_token.write_token.id})",
    "",
    "Monitored Production Token:",
    "  Name: ${pyvider_timed_token.monitored_token.name}",
    "  ID: ${pyvider_timed_token.monitored_token.id}",
    "  Expires: ${pyvider_timed_token.monitored_token.expires_at}",
    "",
    "⚠️  All tokens are time-limited and will expire automatically.",
    "⚠️  Token values are sensitive and stored securely.",
    "⚠️  Plan for token rotation before expiration.",
    "",
    "Registry generated at: ${timestamp()}"
  ])
}

output "basic_token_examples" {
  description = "Information about created tokens (sensitive values excluded)"
  value = {
    tokens_created = {
      simple = {
        name = pyvider_timed_token.simple.name
        id = pyvider_timed_token.simple.id
        expires_at = pyvider_timed_token.simple.expires_at
        token_available = pyvider_timed_token.simple.token != null
      }

      api_auth = {
        name = pyvider_timed_token.api_auth.name
        id = pyvider_timed_token.api_auth.id
        expires_at = pyvider_timed_token.api_auth.expires_at
        token_available = pyvider_timed_token.api_auth.token != null
      }

      service_auth = {
        name = pyvider_timed_token.service_auth.name
        id = pyvider_timed_token.service_auth.id
        expires_at = pyvider_timed_token.service_auth.expires_at
        token_available = pyvider_timed_token.service_auth.token != null
      }

      read_access = {
        name = pyvider_timed_token.read_token.name
        id = pyvider_timed_token.read_token.id
        expires_at = pyvider_timed_token.read_token.expires_at
        token_available = pyvider_timed_token.read_token.token != null
      }

      write_access = {
        name = pyvider_timed_token.write_token.name
        id = pyvider_timed_token.write_token.id
        expires_at = pyvider_timed_token.write_token.expires_at
        token_available = pyvider_timed_token.write_token.token != null
      }

      monitored = {
        name = pyvider_timed_token.monitored_token.name
        id = pyvider_timed_token.monitored_token.id
        expires_at = pyvider_timed_token.monitored_token.expires_at
        token_available = pyvider_timed_token.monitored_token.token != null
      }
    }

    summary = {
      total_tokens = 6
      all_tokens_valid = (
        pyvider_timed_token.simple.token != null &&
        pyvider_timed_token.api_auth.token != null &&
        pyvider_timed_token.service_auth.token != null &&
        pyvider_timed_token.read_token.token != null &&
        pyvider_timed_token.write_token.token != null &&
        pyvider_timed_token.monitored_token.token != null
      )
    }

    files_created = [
      pyvider_file_content.api_config.filename,
      pyvider_file_content.service_config.filename,
      pyvider_file_content.access_control.filename,
      pyvider_file_content.token_monitoring.filename,
      pyvider_file_content.token_registry.filename
    ]
  }
}