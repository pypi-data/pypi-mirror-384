---
page_title: "Function: format"
description: |-
  Formats a string template using positional arguments with error handling
---

# format (Function)

> Formats a string template by substituting positional arguments with null-safe handling and error validation

The `format` function takes a template string with placeholders and a list of values, then returns a formatted string with the placeholders replaced by the corresponding values. It automatically converts values to strings and provides clear error messages for formatting issues.

## When to Use This

- **Message templating**: Create formatted messages with dynamic content
- **Path construction**: Build complex paths with multiple variables
- **Configuration generation**: Generate configuration strings with parameters
- **Report formatting**: Create formatted reports with data
- **SQL/query building**: Construct queries with parameters

**Anti-patterns (when NOT to use):**
- Simple string concatenation (use interpolation instead)
- Complex templating (use dedicated template engines)
- When placeholder count doesn't match value count
- Security-sensitive contexts without proper validation

## Quick Start

```terraform
# Simple message formatting
locals {
  name = "Alice"
  age = 30
  message = provider::pyvider::format("Hello {}, you are {} years old!", [local.name, local.age])
  # Returns: "Hello Alice, you are 30 years old!"
}

# Path formatting
locals {
  env = "production"
  service = "api"
  log_path = provider::pyvider::format("/var/log/{}/{}.log", [local.env, local.service])
  # Returns: "/var/log/production/api.log"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Configuration Generation

{{ example("configuration_generation") }}

### Report Formatting

{{ example("report_formatting") }}

### Error Handling

{{ example("error_handling") }}

## Signature

`format(template: string, values: list[any]) -> string`

## Arguments

- **`template`** (string, required) - The template string with `{}` placeholders for substitution. Returns `null` if this value is `null`.
- **`values`** (list[any], required) - A list of values to substitute into the template. Each value is automatically converted to a string. Can be `null` or empty list.

## Return Value

Returns a formatted string with placeholders replaced by values:
- Each value is converted to a string using `tostring()`
- Placeholders are filled in order: first `{}` gets `values[0]`, second `{}` gets `values[1]`, etc.
- Returns `null` if the template is `null`
- **Raises an error** if there are more placeholders than values

## Error Handling

### Insufficient Values
```terraform
# This will cause an error
locals {
  # Error: not enough values for template
  # bad_format = provider::pyvider::format("Hello {} and {}", ["Alice"])
}

# Safe formatting with validation
variable "names" {
  type = list(string)
  validation {
    condition     = length(var.names) >= 2
    error_message = "At least 2 names required."
  }
}

locals {
  greeting = provider::pyvider::format("Hello {} and {}", var.names)
}
```

### Null Safety
```terraform
locals {
  # These return null
  result1 = provider::pyvider::format(null, ["value"])     # null
  result2 = provider::pyvider::format("template", null)    # Uses empty list
}
```

## Common Patterns

### Configuration File Generation
```terraform
variable "database_config" {
  type = object({
    host = string
    port = number
    name = string
    user = string
  })
}

locals {
  db_url = provider::pyvider::format(
    "postgresql://{}@{}:{}/{}",
    [var.database_config.user, var.database_config.host, var.database_config.port, var.database_config.name]
  )
}

resource "pyvider_file_content" "db_config" {
  filename = "/tmp/database.env"
  content  = "DATABASE_URL=${local.db_url}"
}
```

### Logging and Monitoring
```terraform
variable "service_metrics" {
  type = object({
    requests_per_second = number
    error_rate = number
    latency_ms = number
  })
}

locals {
  metrics_summary = provider::pyvider::format(
    "Service Metrics: {} req/s, {}% errors, {}ms latency",
    [var.service_metrics.requests_per_second, var.service_metrics.error_rate, var.service_metrics.latency_ms]
  )
}
```

### File Path Generation
```terraform
variable "deployment" {
  type = object({
    environment = string
    service     = string
    version     = string
  })
}

locals {
  deployment_path = provider::pyvider::format(
    "/deployments/{}/{}/v{}",
    [var.deployment.environment, var.deployment.service, var.deployment.version]
  )
}
```

## Best Practices

### 1. Validate Value Count
```terraform
variable "template_values" {
  type = list(string)
}

locals {
  # Count placeholders in template
  template = "Processing {} items from {} source"
  expected_count = 2

  # Validate before formatting
  formatted = length(var.template_values) >= local.expected_count ?
    provider::pyvider::format(local.template, var.template_values) :
    "Invalid input: insufficient values"
}
```

### 2. Use Meaningful Templates
```terraform
# ✅ Good - clear placeholder meaning
locals {
  clear_template = "User {} logged in from {} at {}"
  message = provider::pyvider::format(local.clear_template, [var.user, var.ip, var.timestamp])
}

# ❌ Avoid - unclear placeholder order
locals {
  unclear_template = "Event: {} {} {} {}"
  # Hard to know which value goes where
}
```

### 3. Handle Different Data Types
```terraform
locals {
  mixed_values = [
    var.string_value,
    var.number_value,
    var.boolean_value
  ]

  formatted = provider::pyvider::format(
    "Config: {}, Count: {}, Enabled: {}",
    local.mixed_values
  )
}
```

## Related Functions

- [`replace`](./replace.md) - Replace specific patterns in strings
- [`join`](./join.md) - Join list elements with delimiters
- [`upper`](./upper.md) - Convert formatted strings to uppercase
- [`lower`](./lower.md) - Convert formatted strings to lowercase
