---
page_title: "Data Source: pyvider_http_api"
description: |-
  Makes HTTP requests and processes responses for infrastructure automation
---

# pyvider_http_api (Data Source)

> Make HTTP requests to external APIs and process responses in Terraform configurations

The `pyvider_http_api` data source allows you to make HTTP requests to external APIs and use the responses in your Terraform configurations. It supports various HTTP methods, custom headers, and provides detailed response information including status codes, headers, and timing.

## When to Use This

- **API integration**: Fetch configuration data from external APIs
- **Service discovery**: Query service registries or configuration endpoints
- **Health checks**: Verify external services are available before deployment
- **Dynamic configuration**: Pull settings from configuration management systems
- **Webhook validation**: Test webhook endpoints before setting up integrations

**Anti-patterns (when NOT to use):**
- Modifying external state (use proper API resources instead)
- Large file downloads (use specialized download tools)
- Real-time monitoring (use dedicated monitoring solutions)
- Authentication flows requiring multiple requests (handle outside Terraform)

## Quick Start

```terraform
# Simple GET request to fetch configuration
data "pyvider_http_api" "config" {
  url = "https://api.example.com/config"
}

# Use the response in other resources
resource "pyvider_file_content" "downloaded_config" {
  filename = "/tmp/api_config.json"
  content  = data.pyvider_http_api.config.response_body
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Advanced HTTP Operations

{{ example("advanced") }}

### API Integration Patterns

{{ example("integration") }}

### Error Handling

{{ example("error_handling") }}

## Schema

{{ schema() }}

## HTTP Methods

The data source supports all standard HTTP methods:

- **GET** (default) - Retrieve data
- **POST** - Send data to the server
- **PUT** - Update existing resources
- **PATCH** - Partial updates
- **DELETE** - Remove resources
- **HEAD** - Get headers only
- **OPTIONS** - Check allowed methods

```terraform
data "pyvider_http_api" "post_example" {
  url    = "https://api.example.com/users"
  method = "POST"
  headers = {
    "Content-Type" = "application/json"
    "Accept"       = "application/json"
  }
}
```

## Request Headers

Custom headers can be added for authentication, content type specification, and API requirements:

```terraform
data "pyvider_http_api" "authenticated" {
  url = "https://api.example.com/protected"
  headers = {
    "Authorization" = "Bearer ${var.api_token}"
    "User-Agent"    = "Terraform/pyvider-components"
    "Accept"        = "application/json"
    "Content-Type"  = "application/json"
  }
  timeout = 60
}
```

## Response Information

The data source provides comprehensive response details:

### Status and Content
- **`status_code`** - HTTP status code (200, 404, 500, etc.)
- **`response_body`** - Full response body as string
- **`content_type`** - Content-Type header value

### Performance Metrics
- **`response_time_ms`** - Response time in milliseconds
- **`response_headers`** - All response headers as a map
- **`header_count`** - Number of response headers

### Error Information
- **`error_message`** - Error description if request failed

## Timeout Configuration

Configure request timeouts to handle slow APIs:

```terraform
data "pyvider_http_api" "slow_api" {
  url     = "https://slow-api.example.com/data"
  timeout = 120  # 2 minutes
}
```

## Common Patterns

### Configuration Management
```terraform
# Fetch environment-specific configuration
data "pyvider_http_api" "env_config" {
  url = "https://config.example.com/environments/${var.environment}"
  headers = {
    "Authorization" = "Bearer ${var.config_api_token}"
  }
}

locals {
  config = jsondecode(data.pyvider_http_api.env_config.response_body)
}
```

### Service Discovery
```terraform
# Discover available services
data "pyvider_http_api" "service_registry" {
  url = "https://consul.example.com/v1/catalog/services"
}

locals {
  services = jsondecode(data.pyvider_http_api.service_registry.response_body)
  has_database = contains(keys(local.services), "database")
}
```

### Health Check Validation
```terraform
# Check if external service is healthy before proceeding
data "pyvider_http_api" "health_check" {
  url = "https://api.example.com/health"
}

locals {
  service_healthy = (
    data.pyvider_http_api.health_check.status_code == 200 &&
    jsondecode(data.pyvider_http_api.health_check.response_body).status == "healthy"
  )
}
```

### API Response Processing
```terraform
# Process JSON API response
data "pyvider_http_api" "user_data" {
  url = "https://jsonplaceholder.typicode.com/users/1"
}

locals {
  user = jsondecode(data.pyvider_http_api.user_data.response_body)
  user_email = local.user.email
  user_company = local.user.company.name
}
```

## Error Handling

Handle different types of errors gracefully:

```terraform
data "pyvider_http_api" "api_call" {
  url = "https://api.example.com/data"
}

locals {
  # Check for various error conditions
  request_succeeded = data.pyvider_http_api.api_call.status_code >= 200 && data.pyvider_http_api.api_call.status_code < 300

  api_response = local.request_succeeded ? jsondecode(data.pyvider_http_api.api_call.response_body) : {}

  fallback_config = {
    default = true
    message = "Using fallback configuration due to API error"
  }

  final_config = local.request_succeeded ? local.api_response : local.fallback_config
}
```

## Security Best Practices

1. **Secure API Keys**: Use variables or environment variables for sensitive tokens
2. **HTTPS Only**: Always use HTTPS URLs for sensitive data
3. **Timeout Limits**: Set reasonable timeouts to prevent hanging
4. **Error Handling**: Don't expose sensitive error details in outputs
5. **Rate Limiting**: Be mindful of API rate limits

```terraform
# Secure API call example
data "pyvider_http_api" "secure_api" {
  url = "https://secure-api.example.com/data"
  headers = {
    "Authorization" = "Bearer ${var.api_token}"  # Use variable, not hardcode
    "User-Agent"    = "MyApp/1.0"
  }
  timeout = 30
}

# Don't expose sensitive data in outputs
output "api_success" {
  value = data.pyvider_http_api.secure_api.status_code == 200
}
```

## Limitations

- **Request Body**: Currently doesn't support request body for POST/PUT requests
- **File Uploads**: Not designed for file upload operations
- **Cookies**: No automatic cookie handling
- **Redirects**: Follows redirects automatically but doesn't expose redirect chain
- **Binary Data**: Response body is treated as text

## Troubleshooting

### Common HTTP Status Codes
- **200 OK** - Success
- **401 Unauthorized** - Check authentication headers
- **403 Forbidden** - Check API permissions
- **404 Not Found** - Verify URL is correct
- **429 Too Many Requests** - API rate limit exceeded
- **500 Internal Server Error** - API server issue

### Connection Issues
```terraform
# Check for connection errors
locals {
  connection_error = data.pyvider_http_api.example.error_message != null
  timeout_occurred = data.pyvider_http_api.example.response_time_ms == null
}
```

## Related Components

- [`pyvider_file_content`](../../resources/file_content.md) - Save API responses to files
- [`pyvider_env_variables`](../env_variables.md) - Use environment variables for API credentials
- [`lens_jq` function](../../functions/lens_jq.md) - Transform API responses with JQ queries