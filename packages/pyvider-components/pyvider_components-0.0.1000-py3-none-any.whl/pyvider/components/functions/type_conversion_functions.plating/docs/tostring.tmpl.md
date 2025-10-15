---
page_title: "Function: tostring"
description: |-
  Explicitly converts values to strings with null-safe handling and boolean normalization
---

# tostring (Function)

> Converts any value to its string representation with null-safe handling and standardized boolean formatting

The `tostring` function takes any value and converts it to a string representation. It handles different data types appropriately, including special formatting for booleans, and provides null-safe conversion.

## When to Use This

- **Template generation**: Convert values for use in string templates
- **File content creation**: Prepare values for writing to configuration files
- **Logging and output**: Format values for display or logging
- **API integration**: Convert values to string format for external APIs
- **Configuration normalization**: Ensure consistent string representation

**Anti-patterns (when NOT to use):**
- Values already known to be strings (unnecessary overhead)
- Complex object serialization (use JSON functions instead)
- When original type information needs to be preserved
- Binary data conversion (use appropriate encoding functions)

## Quick Start

```terraform
# Convert different types to strings
locals {
  number_str = provider::pyvider::tostring(42)          # Returns: "42"
  float_str = provider::pyvider::tostring(3.14)         # Returns: "3.14"
  bool_str = provider::pyvider::tostring(true)          # Returns: "true"
  false_str = provider::pyvider::tostring(false)        # Returns: "false"
}

# Use in template generation
variable "enabled" {
  type = bool
  default = true
}

variable "port" {
  type = number
  default = 8080
}

locals {
  config_template = "enabled=${provider::pyvider::tostring(var.enabled)};port=${provider::pyvider::tostring(var.port)}"
  # Returns: "enabled=true;port=8080"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Configuration File Generation

{{ example("configuration_generation") }}

### Template Processing

{{ example("template_processing") }}

### Data Normalization

{{ example("data_normalization") }}

## Signature

`tostring(value: any) -> string`

## Arguments

- **`value`** (any, required) - The value to convert to a string. Can be any type (number, boolean, string, etc.). Returns `null` if this value is `null`.

## Return Value

Returns the string representation of the value:
- **Numbers**: Converted to decimal string representation (e.g., `42` → `"42"`)
- **Booleans**: Converted to lowercase strings (`true` → `"true"`, `false` → `"false"`)
- **Strings**: Returned unchanged
- **Other types**: Converted using standard string representation
- Returns `null` if the input is `null`

## Type-Specific Behavior

### Numbers
```terraform
locals {
  integer = provider::pyvider::tostring(123)        # "123"
  float = provider::pyvider::tostring(45.67)        # "45.67"
  negative = provider::pyvider::tostring(-89)       # "-89"
  zero = provider::pyvider::tostring(0)             # "0"
}
```

### Booleans
```terraform
locals {
  true_str = provider::pyvider::tostring(true)      # "true"
  false_str = provider::pyvider::tostring(false)    # "false"
}
```

### Strings
```terraform
locals {
  unchanged = provider::pyvider::tostring("hello")  # "hello"
  empty = provider::pyvider::tostring("")           # ""
}
```

### Null Values
```terraform
locals {
  null_result = provider::pyvider::tostring(null)   # null
}
```

## Common Patterns

### Configuration File Generation
```terraform
variable "database_config" {
  type = object({
    host     = string
    port     = number
    ssl      = bool
    timeout  = number
  })
  default = {
    host    = "localhost"
    port    = 5432
    ssl     = true
    timeout = 30
  }
}

locals {
  config_lines = [
    "host=${var.database_config.host}",
    "port=${provider::pyvider::tostring(var.database_config.port)}",
    "ssl=${provider::pyvider::tostring(var.database_config.ssl)}",
    "timeout=${provider::pyvider::tostring(var.database_config.timeout)}"
  ]
}

resource "pyvider_file_content" "db_config" {
  filename = "/tmp/database.conf"
  content  = provider::pyvider::join("\n", local.config_lines)
}
```

### Environment Variable Formatting
```terraform
variable "app_settings" {
  type = object({
    debug_mode   = bool
    max_workers  = number
    api_version  = string
    cache_enabled = bool
  })
}

locals {
  env_vars = {
    DEBUG = provider::pyvider::tostring(var.app_settings.debug_mode)
    WORKERS = provider::pyvider::tostring(var.app_settings.max_workers)
    API_VERSION = var.app_settings.api_version  # Already a string
    CACHE_ENABLED = provider::pyvider::tostring(var.app_settings.cache_enabled)
  }

  env_file_content = provider::pyvider::join("\n", [
    for key, value in local.env_vars : "${key}=${value}"
  ])
}

resource "pyvider_file_content" "env_file" {
  filename = "/tmp/.env"
  content  = local.env_file_content
}
```

### API Payload Preparation
```terraform
variable "service_config" {
  type = object({
    replicas     = number
    auto_scale   = bool
    cpu_limit    = number
    memory_limit = number
  })
}

locals {
  # Convert all values to strings for API submission
  api_payload = {
    "replicas"     = provider::pyvider::tostring(var.service_config.replicas)
    "auto_scale"   = provider::pyvider::tostring(var.service_config.auto_scale)
    "cpu_limit"    = provider::pyvider::tostring(var.service_config.cpu_limit)
    "memory_limit" = provider::pyvider::tostring(var.service_config.memory_limit)
  }

  payload_json = jsonencode(local.api_payload)
}

resource "pyvider_file_content" "api_request" {
  filename = "/tmp/service_config.json"
  content  = local.payload_json
}
```

### Log Message Formatting
```terraform
variable "deployment_info" {
  type = object({
    version     = string
    instance_count = number
    health_check = bool
    timestamp   = string
  })
}

locals {
  log_message = provider::pyvider::format(
    "Deployment {} completed: {} instances, health_check={}, at {}",
    [
      var.deployment_info.version,
      provider::pyvider::tostring(var.deployment_info.instance_count),
      provider::pyvider::tostring(var.deployment_info.health_check),
      var.deployment_info.timestamp
    ]
  )
}

resource "pyvider_file_content" "deployment_log" {
  filename = "/tmp/deployment.log"
  content  = local.log_message
}
```

### Conditional String Building
```terraform
variable "feature_flags" {
  type = map(bool)
  default = {
    analytics = true
    debugging = false
    beta_ui   = true
  }
}

locals {
  # Convert boolean flags to string representations
  enabled_features = [
    for feature, enabled in var.feature_flags :
    "${feature}=${provider::pyvider::tostring(enabled)}" if enabled
  ]

  feature_config = provider::pyvider::join(",", local.enabled_features)
}

resource "pyvider_file_content" "features" {
  filename = "/tmp/enabled_features.txt"
  content  = "Enabled features: ${local.feature_config}"
}
```

## Best Practices

### 1. Use for Mixed-Type Templates
```terraform
# Good - explicit conversion for clarity
locals {
  mixed_config = "timeout=${provider::pyvider::tostring(var.timeout)};enabled=${provider::pyvider::tostring(var.enabled)}"
}

# Avoid - relying on implicit conversion
locals {
  # This works but is less explicit
  implicit_config = "timeout=${var.timeout};enabled=${var.enabled}"
}
```

### 2. Handle Null Values
```terraform
locals {
  safe_conversion = var.optional_value != null ? provider::pyvider::tostring(var.optional_value) : "default"
}
```

### 3. Use with Format Functions
```terraform
locals {
  # Combine with format for complex templates
  status_message = provider::pyvider::format(
    "Service status: running={}, instances={}, port={}",
    [
      provider::pyvider::tostring(var.service_running),
      provider::pyvider::tostring(var.instance_count),
      provider::pyvider::tostring(var.service_port)
    ]
  )
}
```

### 4. Validate Types When Necessary
```terraform
variable "numeric_setting" {
  type = number
  validation {
    condition     = var.numeric_setting >= 0
    error_message = "Setting must be non-negative."
  }
}

locals {
  setting_string = provider::pyvider::tostring(var.numeric_setting)
}
```

## Performance Considerations

- **Lightweight operation**: String conversion is fast for primitive types
- **Memory efficient**: Creates new string objects only when necessary
- **Type checking**: Minimal overhead for type detection
- **Boolean optimization**: Special handling for consistent boolean representation

## Related Functions

- [`format`](../string_manipulation/format.md) - Format strings with converted values
- [`join`](../string_manipulation/join.md) - Join converted values into strings
- [`replace`](../string_manipulation/replace.md) - Replace patterns in converted strings
- [`upper`](../string_manipulation/upper.md) - Convert case of string results
- [`lower`](../string_manipulation/lower.md) - Convert case of string results
