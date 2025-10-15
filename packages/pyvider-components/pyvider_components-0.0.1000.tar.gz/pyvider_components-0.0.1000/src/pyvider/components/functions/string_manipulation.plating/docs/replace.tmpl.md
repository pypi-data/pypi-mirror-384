---
page_title: "Function: replace"
description: |-
  Replaces all occurrences of a substring with another string
---

# replace (Function)

> Replaces all occurrences of a search string with a replacement string with null-safe handling

The `replace` function searches for all occurrences of a substring within a string and replaces them with a replacement string. It handles null values gracefully and performs global replacement (all occurrences).

## When to Use This

- **Text normalization**: Replace unwanted characters or patterns
- **Path manipulation**: Convert path separators or modify paths
- **Configuration templating**: Replace placeholders in configuration templates
- **Data cleaning**: Remove or replace invalid characters
- **URL manipulation**: Modify URLs or endpoints

**Anti-patterns (when NOT to use):**
- Complex pattern matching (use regex-capable tools)
- Single character replacement in long strings (consider performance)
- Binary data manipulation
- Case-sensitive replacements when case-insensitive is needed

## Quick Start

```terraform
# Simple text replacement
locals {
  template = "Hello PLACEHOLDER, welcome!"
  message = provider::pyvider::replace(local.template, "PLACEHOLDER", "World")  # Returns: "Hello World, welcome!"
}

# Path separator conversion
locals {
  windows_path = "C:\\Program Files\\MyApp"
  unix_path = provider::pyvider::replace(local.windows_path, "\\", "/")  # Returns: "C:/Program Files/MyApp"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Configuration Templating

{{ example("configuration_templating") }}

### Path Manipulation

{{ example("path_manipulation") }}

### Data Cleaning

{{ example("data_cleaning") }}

## Signature

`replace(string: string, search: string, replacement: string) -> string`

## Arguments

- **`string`** (string, required) - The string to search within. Returns `null` if this value is `null`.
- **`search`** (string, required) - The substring to search for. Uses empty string if `null`.
- **`replacement`** (string, required) - The string to replace matches with. Uses empty string if `null`.

## Return Value

Returns a new string with all occurrences of the search string replaced:
- Replaces ALL occurrences (global replacement)
- Case-sensitive matching
- Returns the original string if no matches found
- Returns `null` if the input string is `null`
- Empty search string returns original string unchanged

## Behavior Details

### Global Replacement
```terraform
locals {
  text = "The quick brown fox jumps over the lazy dog"
  result = provider::pyvider::replace(local.text, "the", "THE")  # Returns: "The quick brown fox jumps over THE lazy dog"
}
```

### Empty String Handling
```terraform
locals {
  # Remove all spaces
  no_spaces = provider::pyvider::replace("hello world", " ", "")  # Returns: "helloworld"

  # Add prefix to non-empty string
  prefixed = provider::pyvider::replace("value", "", "prefix-")  # Returns: "value" (no change)
}
```

## Common Patterns

### Configuration Template Processing
```terraform
variable "database_host" {
  type = string
  default = "localhost"
}

variable "database_port" {
  type = string
  default = "5432"
}

locals {
  config_template = "host={{DB_HOST}};port={{DB_PORT}};ssl=true"
  config_with_host = provider::pyvider::replace(local.config_template, "{{DB_HOST}}", var.database_host)
  final_config = provider::pyvider::replace(local.config_with_host, "{{DB_PORT}}", var.database_port)
}

resource "pyvider_file_content" "db_config" {
  filename = "/tmp/database.conf"
  content  = local.final_config
}
```

### URL Endpoint Modification
```terraform
variable "base_url" {
  type = string
  default = "https://api.example.com/v1/users"
}

variable "new_version" {
  type = string
  default = "v2"
}

locals {
  updated_url = provider::pyvider::replace(var.base_url, "/v1/", "/${var.new_version}/")
}
```

### Data Sanitization
```terraform
variable "user_input" {
  type = string
}

locals {
  # Remove potentially dangerous characters
  step1 = provider::pyvider::replace(var.user_input, "<", "")
  step2 = provider::pyvider::replace(local.step1, ">", "")
  sanitized = provider::pyvider::replace(local.step2, "&", "")
}
```

## Best Practices

### 1. Chain Replacements for Multiple Substitutions
```terraform
locals {
  template = "{{NAME}} works at {{COMPANY}} in {{CITY}}"
  step1 = provider::pyvider::replace(local.template, "{{NAME}}", var.name)
  step2 = provider::pyvider::replace(local.step1, "{{COMPANY}}", var.company)
  final = provider::pyvider::replace(local.step2, "{{CITY}}", var.city)
}
```

### 2. Validate Inputs
```terraform
variable "text_to_clean" {
  type = string
  validation {
    condition     = length(var.text_to_clean) > 0
    error_message = "Input text cannot be empty."
  }
}

locals {
  cleaned = provider::pyvider::replace(var.text_to_clean, "bad_pattern", "good_pattern")
}
```

### 3. Handle Null Values
```terraform
locals {
  safe_replace = var.optional_string != null ? provider::pyvider::replace(var.optional_string, "old", "new") : null
}
```

## Related Functions

- [`format`](./format.md) - Format strings with placeholders (alternative to multiple replacements)
- [`split`](./split.md) - Split strings before processing parts
- [`join`](./join.md) - Join strings after replacement
- [`upper`](./upper.md) - Convert case before replacement
- [`lower`](./lower.md) - Convert case before replacement
