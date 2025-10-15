---
page_title: "Resource: pyvider_timed_token"
description: |-
  Generates time-limited authentication tokens with automatic expiration management
---

# pyvider_timed_token (Resource)

> Generate secure, time-limited tokens for authentication and authorization workflows

The `pyvider_timed_token` resource creates time-limited authentication tokens that automatically expire after a specified duration. This is useful for generating temporary access credentials, API keys, or session tokens with built-in security through automatic expiration.

## When to Use This

- **Temporary API access**: Generate short-lived tokens for external integrations
- **Session management**: Create time-limited session tokens for applications
- **Secure automation**: Provide temporary credentials for CI/CD pipelines
- **Token rotation**: Implement automatic token refresh workflows
- **Testing and development**: Generate test tokens with predictable expiration

**Anti-patterns (when NOT to use):**
- Long-term authentication (use proper credential management instead)
- Storing tokens in version control (tokens are sensitive)
- Client-side token generation (generate server-side for security)
- Permanent access tokens (defeats the purpose of time-limited security)

## Quick Start

```terraform
# Generate a simple timed token
resource "pyvider_timed_token" "api_access" {
  name = "temporary-api-token"
}

# Use the token in other resources
resource "pyvider_file_content" "api_config" {
  filename = "/tmp/api_config.json"
  content = jsonencode({
    api_token = pyvider_timed_token.api_access.token
    expires_at = pyvider_timed_token.api_access.expires_at
  })
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### CI/CD Pipeline Tokens

{{ example("cicd") }}

### API Integration Tokens

{{ example("api_integration") }}

### Multi-Environment Tokens

{{ example("multi_environment") }}

## Schema

{{ schema() }}

## Token Lifecycle

The `pyvider_timed_token` resource manages the complete lifecycle of time-limited tokens:

### 1. Creation
- Generates a unique token ID with UUID format
- Creates a secure token string with `token-{uuid}` format
- Sets expiration time to 1 hour from creation
- Stores sensitive data in encrypted private state

### 2. Reading
- Returns current token and expiration information
- Automatically decrypts private state for access
- Maintains token validity status

### 3. Expiration
- Tokens expire automatically after the specified duration
- No cleanup required - tokens are self-invalidating
- Expiration time is stored in ISO 8601 format

### 4. Deletion
- Removes token from Terraform state
- No additional cleanup required on the provider side

## Security Features

### Sensitive Data Protection
```terraform
resource "pyvider_timed_token" "secure_token" {
  name = "production-api-key"
}

# ✅ Safe - token is marked as sensitive
output "token_available" {
  value = pyvider_timed_token.secure_token.token != null
}

# ❌ Unsafe - would expose sensitive token
# output "actual_token" {
#   value = pyvider_timed_token.secure_token.token
# }
```

### Private State Encryption
The resource uses Terraform's private state encryption to securely store:
- The actual token value
- Expiration timestamp
- Internal token metadata

### Token Format
Tokens follow a predictable but secure format:
- **ID**: `timed-token-id-{uuid}`
- **Token**: `token-{uuid}`
- **Expiration**: ISO 8601 timestamp (UTC)

## Common Patterns

### Token Rotation Strategy
```terraform
# Create multiple tokens for rotation
resource "pyvider_timed_token" "primary" {
  name = "primary-token"
}

resource "pyvider_timed_token" "backup" {
  name = "backup-token"
}

# Application config with fallback
resource "pyvider_file_content" "app_config" {
  filename = "/app/config/tokens.json"
  content = jsonencode({
    primary_token = {
      value = pyvider_timed_token.primary.token
      expires_at = pyvider_timed_token.primary.expires_at
    }
    backup_token = {
      value = pyvider_timed_token.backup.token
      expires_at = pyvider_timed_token.backup.expires_at
    }
  })
}
```

### Environment-Specific Tokens
```terraform
variable "environment" {
  description = "Deployment environment"
  type        = string
}

resource "pyvider_timed_token" "env_token" {
  name = "${var.environment}-api-token"
}

# Different expiration handling per environment
locals {
  token_config = {
    production = {
      require_rotation = true
      max_age_hours = 1
    }
    staging = {
      require_rotation = false
      max_age_hours = 24
    }
    development = {
      require_rotation = false
      max_age_hours = 168  # 1 week
    }
  }
}
```

### Integration with External Systems
```terraform
resource "pyvider_timed_token" "webhook_token" {
  name = "webhook-authentication"
}

# Configure webhook with temporary token
data "pyvider_http_api" "register_webhook" {
  url    = "https://api.example.com/webhooks"
  method = "POST"
  headers = {
    "Authorization" = "Bearer ${pyvider_timed_token.webhook_token.token}"
    "Content-Type"  = "application/json"
  }
}
```

### Token Monitoring and Alerts
```terraform
resource "pyvider_timed_token" "monitored_token" {
  name = "critical-service-token"
}

# Create monitoring configuration
resource "pyvider_file_content" "token_monitor" {
  filename = "/monitoring/token_status.json"
  content = jsonencode({
    token_id = pyvider_timed_token.monitored_token.id
    name = pyvider_timed_token.monitored_token.name
    expires_at = pyvider_timed_token.monitored_token.expires_at
    monitoring = {
      alert_before_expiry_minutes = 15
      auto_rotate = true
      notification_webhook = "https://alerts.example.com/webhook"
    }
  })
}
```

## Error Handling

### Token Access Validation
```terraform
resource "pyvider_timed_token" "api_token" {
  name = "service-integration"
}

# Validate token is available before use
locals {
  token_valid = (
    pyvider_timed_token.api_token.token != null &&
    pyvider_timed_token.api_token.expires_at != null
  )
}

# Conditional resource creation
resource "pyvider_file_content" "api_config" {
  count = local.token_valid ? 1 : 0

  filename = "/config/api_credentials.json"
  content = jsonencode({
    token = pyvider_timed_token.api_token.token
    expires_at = pyvider_timed_token.api_token.expires_at
    last_updated = timestamp()
  })
}
```

### Expiration Handling
```terraform
resource "pyvider_timed_token" "time_sensitive" {
  name = "batch-job-token"
}

# Create expiration warning file
resource "pyvider_file_content" "expiration_notice" {
  filename = "/tmp/token_expiration_notice.txt"
  content = join("\n", [
    "Token Expiration Notice",
    "=====================",
    "Token Name: ${pyvider_timed_token.time_sensitive.name}",
    "Token ID: ${pyvider_timed_token.time_sensitive.id}",
    "Expires At: ${pyvider_timed_token.time_sensitive.expires_at}",
    "",
    "⚠️  This token will expire automatically.",
    "⚠️  Plan for token rotation before expiration.",
    "⚠️  Monitor application logs for authentication failures.",
    "",
    "Generated: ${timestamp()}"
  ])
}
```

## Best Practices

### 1. Descriptive Naming
```terraform
# ✅ Good - descriptive names
resource "pyvider_timed_token" "github_actions_deploy" {
  name = "github-actions-deployment-token"
}

resource "pyvider_timed_token" "api_gateway_auth" {
  name = "api-gateway-service-auth"
}

# ❌ Bad - generic names
resource "pyvider_timed_token" "token1" {
  name = "token"
}
```

### 2. Token Scope Documentation
```terraform
resource "pyvider_timed_token" "database_migration" {
  name = "db-migration-readonly-token"

  # Document token purpose in configuration
  lifecycle {
    # This token is used for database migration scripts
    # Scope: Read-only access to production database
    # Duration: 1 hour (automatic expiration)
    # Rotation: Manual, as needed for migrations
    ignore_changes = []
  }
}
```

### 3. Environment Isolation
```terraform
variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

resource "pyvider_timed_token" "env_isolated" {
  name = "${var.environment}-service-token"
}

# Environment-specific handling
locals {
  is_production = var.environment == "prod"

  # Production tokens require additional monitoring
  monitoring_required = local.is_production
}
```

### 4. Token Rotation Planning
```terraform
# Create tokens with rotation metadata
resource "pyvider_timed_token" "rotatable" {
  name = "service-api-token-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
}

# Track token generations
resource "pyvider_file_content" "token_registry" {
  filename = "/registry/token_generations.json"
  content = jsonencode({
    current_generation = {
      token_id = pyvider_timed_token.rotatable.id
      created_at = timestamp()
      expires_at = pyvider_timed_token.rotatable.expires_at
    }
    rotation_policy = {
      automatic = false
      advance_notice_minutes = 30
      fallback_strategy = "maintain_previous_token"
    }
  })
}
```

## Troubleshooting

### Common Issues

**Issue**: Token appears to be null or empty
**Solution**: Check that the resource has been created successfully
```terraform
# Debug token creation
output "token_debug" {
  value = {
    token_exists = pyvider_timed_token.debug.token != null
    id_exists = pyvider_timed_token.debug.id != null
    name = pyvider_timed_token.debug.name
  }
}
```

**Issue**: Cannot access token value in outputs
**Solution**: Token is marked as sensitive; use conditional checks instead
```terraform
# ✅ Correct way to check token
output "token_status" {
  value = {
    available = pyvider_timed_token.example.token != null
    has_expiration = pyvider_timed_token.example.expires_at != null
  }
}
```

**Issue**: Token expiration time format confusion
**Solution**: Expiration is in ISO 8601 format (UTC)
```terraform
# Parse expiration time
locals {
  expires_timestamp = pyvider_timed_token.example.expires_at
  # Format: "2024-01-15T14:30:00.000000+00:00"
}
```

## Related Components

- [`pyvider_private_state_verifier`](../private_state_verifier.md) - Verify private state encryption
- [`pyvider_file_content`](../file_content.md) - Store token configuration files
- [`pyvider_http_api`](../../data_sources/http_api.md) - Use tokens for API authentication
- [`pyvider_env_variables`](../../data_sources/env_variables.md) - Read token configuration from environment