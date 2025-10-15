---
page_title: "Function: upper"
description: |-
  Converts a string to uppercase with null-safe handling
---

# upper (Function)

> Converts all characters in a string to uppercase with null-safe handling

The `upper` function takes a string and returns a new string with all alphabetic characters converted to uppercase. It handles null values gracefully by returning null when the input is null.

## When to Use This

- **Case normalization**: Standardize text case for comparisons
- **Display formatting**: Format text for headers or emphasis
- **Data consistency**: Normalize user input or imported data
- **Configuration values**: Standardize environment or configuration strings
- **Search operations**: Normalize text for case-insensitive matching

**Anti-patterns (when NOT to use):**
- Preserving original case formatting (use original string)
- Binary data or non-text content
- When case sensitivity is required
- Passwords or security-sensitive strings

## Quick Start

```terraform
# Simple case conversion
locals {
  environment = "production"
  env_upper = provider::pyvider::upper(local.environment)  # Returns: "PRODUCTION"
}

# Normalizing user input
variable "region_name" {
  default = "us-west-2"
}

locals {
  region_normalized = provider::pyvider::upper(var.region_name)  # Returns: "US-WEST-2"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Configuration Normalization

{{ example("configuration_normalization") }}

### Text Processing

{{ example("text_processing") }}

### Null Handling

{{ example("null_handling") }}

## Signature

`upper(input_str: string) -> string`

## Arguments

- **`input_str`** (string, required) - The string to convert to uppercase. Returns `null` if this value is `null`.

## Return Value

Returns a new string with all alphabetic characters converted to uppercase:
- Non-alphabetic characters (numbers, symbols, spaces) remain unchanged
- Returns `null` if the input is `null`
- Returns an empty string if the input is an empty string

## Common Patterns

### Environment Variables
```terraform
variable "env" {
  type = string
  default = "dev"
}

locals {
  environment_upper = provider::pyvider::upper(var.env)
}

resource "pyvider_file_content" "config" {
  filename = "/tmp/app_config.env"
  content  = "ENVIRONMENT=${local.environment_upper}"
}
```

### Header Formatting
```terraform
variable "service_name" {
  type = string
}

locals {
  header_text = provider::pyvider::upper(var.service_name)
}

resource "pyvider_file_content" "header" {
  filename = "/tmp/service_header.txt"
  content  = "=== ${local.header_text} SERVICE ==="
}
```

### Case-Insensitive Comparisons
```terraform
variable "user_input" {
  type = string
}

locals {
  normalized_input = provider::pyvider::upper(var.user_input)
  is_production = local.normalized_input == "PRODUCTION"
}
```

## Best Practices

### 1. Handle Null Values
```terraform
locals {
  safe_upper = var.optional_string != null ? provider::pyvider::upper(var.optional_string) : null
}
```

### 2. Validate Input Type
```terraform
variable "text_input" {
  type = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]*$", var.text_input))
    error_message = "Input must contain only alphanumeric characters, underscores, and hyphens."
  }
}

locals {
  normalized_text = provider::pyvider::upper(var.text_input)
}
```

## Related Functions

- [`lower`](./lower.md) - Convert string to lowercase
- [`format`](./format.md) - Format strings with placeholders
- [`replace`](./replace.md) - Replace text patterns in strings
- [`split`](./split.md) - Split strings into lists
- [`join`](./join.md) - Join lists into strings
