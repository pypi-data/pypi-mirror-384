---
page_title: "Data Source: pyvider_provider_config_reader"
description: |-
  Reads provider configuration settings for dynamic resource management
---

# pyvider_provider_config_reader (Data Source)

> Access provider configuration settings within your Terraform configuration

The `pyvider_provider_config_reader` data source allows you to read the current provider configuration settings. This enables dynamic resource creation based on provider settings and helps create reusable configurations that adapt to different provider configurations.

## When to Use This

- **Dynamic resource configuration**: Adapt resource settings based on provider config
- **Multi-environment deployments**: Use different API endpoints per environment
- **Configuration validation**: Verify provider settings before resource creation
- **Debugging and troubleshooting**: Inspect current provider configuration
- **Conditional logic**: Create resources based on provider capabilities

**Anti-patterns (when NOT to use):**
- Storing sensitive data in outputs (API tokens are marked sensitive)
- Hardcoding provider configuration (defeats the purpose)
- Using for application configuration (use proper config management)

## Quick Start

```terraform
# Read current provider configuration
data "pyvider_provider_config_reader" "current" {}

# Use provider config in resource creation
resource "pyvider_file_content" "config_summary" {
  filename = "/tmp/provider_config.txt"
  content = "API Endpoint: ${data.pyvider_provider_config_reader.current.api_endpoint}"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Conditional Resource Creation

{{ example("conditional") }}

### Multi-Provider Setup

{{ example("multi_provider") }}

## Schema

{{ schema() }}

## Provider Configuration Attributes

The data source exposes the following provider configuration settings:

### Connection Settings
- **`api_endpoint`** - The API endpoint URL configured for the provider
- **`api_timeout`** - Request timeout in seconds
- **`api_retries`** - Number of retry attempts for failed requests

### Authentication
- **`api_token`** - API authentication token (marked as sensitive)
- **`api_headers`** - Custom headers sent with API requests

### Security Settings
- **`api_insecure_skip_verify`** - Whether TLS certificate verification is disabled

## Common Patterns

### Environment-Aware Configuration
```terraform
data "pyvider_provider_config_reader" "config" {}

locals {
  # Determine environment based on API endpoint
  environment = (
    can(regex("staging", data.pyvider_provider_config_reader.config.api_endpoint)) ? "staging" :
    can(regex("prod", data.pyvider_provider_config_reader.config.api_endpoint)) ? "production" :
    "development"
  )

  # Adjust settings based on environment
  replica_count = local.environment == "production" ? 3 : 1
  debug_enabled = local.environment == "development"
}
```

### Configuration Validation
```terraform
data "pyvider_provider_config_reader" "config" {}

locals {
  # Validate provider configuration
  config_valid = (
    data.pyvider_provider_config_reader.config.api_endpoint != null &&
    data.pyvider_provider_config_reader.config.api_timeout > 0 &&
    data.pyvider_provider_config_reader.config.api_retries >= 0
  )

  # Configuration warnings
  config_warnings = concat(
    data.pyvider_provider_config_reader.config.api_insecure_skip_verify ? ["TLS verification disabled"] : [],
    data.pyvider_provider_config_reader.config.api_timeout > 300 ? ["Very long timeout configured"] : [],
    data.pyvider_provider_config_reader.config.api_retries > 10 ? ["High retry count may cause delays"] : []
  )
}
```

### Conditional Resource Creation
```terraform
data "pyvider_provider_config_reader" "config" {}

# Only create certain resources if provider supports them
resource "pyvider_file_content" "debug_config" {
  count = data.pyvider_provider_config_reader.config.api_timeout > 60 ? 1 : 0

  filename = "/tmp/debug_enabled.conf"
  content  = "Debug mode enabled due to high timeout value"
}
```

### API Client Configuration
```terraform
data "pyvider_provider_config_reader" "config" {}

# Configure API client based on provider settings
resource "pyvider_file_content" "api_client_config" {
  filename = "/tmp/api_client.json"
  content = jsonencode({
    endpoint = data.pyvider_provider_config_reader.config.api_endpoint
    timeout  = data.pyvider_provider_config_reader.config.api_timeout
    retries  = data.pyvider_provider_config_reader.config.api_retries
    headers  = data.pyvider_provider_config_reader.config.api_headers

    # Don't expose sensitive token
    auth_configured = data.pyvider_provider_config_reader.config.api_token != null

    security = {
      tls_verify = !data.pyvider_provider_config_reader.config.api_insecure_skip_verify
    }
  })
}
```

## Security Considerations

1. **Sensitive Data**: The `api_token` is marked as sensitive and won't appear in logs
2. **Output Exposure**: Be careful not to expose sensitive configuration in outputs
3. **TLS Verification**: Check `api_insecure_skip_verify` for security implications
4. **Header Inspection**: Custom headers may contain sensitive information

```terraform
# ✅ Safe - doesn't expose sensitive data
output "provider_endpoint" {
  value = data.pyvider_provider_config_reader.config.api_endpoint
}

# ❌ Unsafe - would expose sensitive token
# output "provider_token" {
#   value = data.pyvider_provider_config_reader.config.api_token
# }

# ✅ Safe - checks if token exists without exposing it
output "auth_configured" {
  value = data.pyvider_provider_config_reader.config.api_token != null
}
```

## Multi-Provider Scenarios

When using multiple provider instances, each instance's configuration can be read separately:

```terraform
# Configure multiple provider instances
provider "pyvider" {
  alias        = "staging"
  api_endpoint = "https://staging-api.example.com"
  api_timeout  = 30
}

provider "pyvider" {
  alias        = "production"
  api_endpoint = "https://api.example.com"
  api_timeout  = 60
}

# Read configuration from each provider
data "pyvider_provider_config_reader" "staging" {
  provider = pyvider.staging
}

data "pyvider_provider_config_reader" "production" {
  provider = pyvider.production
}

# Compare configurations
locals {
  staging_timeout    = data.pyvider_provider_config_reader.staging.api_timeout
  production_timeout = data.pyvider_provider_config_reader.production.api_timeout

  timeout_difference = local.production_timeout - local.staging_timeout
}
```

## Troubleshooting

### Common Issues

**Error: "Provider context has not been configured"**
- Ensure the provider block is properly configured
- Check that required provider configuration is present

**Missing Configuration Values**
- Some attributes may be null if not configured in the provider block
- Use conditional logic to handle missing values

**Sensitive Data in Outputs**
- Terraform will prevent sensitive values from being displayed
- Use conditional checks instead of direct value access

### Debugging Provider Configuration
```terraform
data "pyvider_provider_config_reader" "debug" {}

resource "pyvider_file_content" "provider_debug" {
  filename = "/tmp/provider_debug.txt"
  content = join("\n", [
    "Provider Configuration Debug Info:",
    "================================",
    "Endpoint configured: ${data.pyvider_provider_config_reader.debug.api_endpoint != null}",
    "Timeout value: ${data.pyvider_provider_config_reader.debug.api_timeout}",
    "Retries configured: ${data.pyvider_provider_config_reader.debug.api_retries}",
    "TLS verification: ${!data.pyvider_provider_config_reader.debug.api_insecure_skip_verify}",
    "Custom headers: ${length(data.pyvider_provider_config_reader.debug.api_headers != null ? data.pyvider_provider_config_reader.debug.api_headers : {})}",
    "Authentication: ${data.pyvider_provider_config_reader.debug.api_token != null ? "Configured" : "Not configured"}",
  ])
}
```

## Related Components

- [`pyvider_env_variables`](../env_variables.md) - Read environment variables used in provider configuration
- [`pyvider_http_api`](../http_api.md) - Make requests using provider's configured endpoint
- [`pyvider_file_content`](../../resources/file_content.md) - Create configuration files based on provider settings