---
page_title: "Function: lower"
description: |-
  Converts a string to lowercase with null-safe handling
---

# lower (Function)

> Converts all characters in a string to lowercase with null-safe handling

The `lower` function converts all alphabetic characters in a string to lowercase. It's commonly used for case-insensitive comparisons, normalization, and ensuring consistent formatting.

## When to Use This

- **Case-insensitive comparisons**: Normalize strings before comparison
- **Configuration keys**: Create consistent lowercase identifiers
- **Search operations**: Normalize search terms for matching
- **Environment variables**: Process case-insensitive environment names
- **File extensions**: Ensure consistent lowercase extensions

**Anti-patterns (when NOT to use):**
- When case distinction is important (e.g., passwords)
- For display text that requires proper casing
- When working with case-sensitive systems

## Quick Start

```terraform
# Simple lowercase conversion
locals {
  environment = provider::pyvider::lower("PRODUCTION")  # Returns: "production"
}

# Normalize user input
variable "user_input" {
  default = "John.DOE@EXAMPLE.COM"
}

locals {
  normalized_email = provider::pyvider::lower(var.user_input)  # Returns: "john.doe@example.com"
}
```

## Examples

{{ example("basic") }}

### Common Use Cases

```terraform
# Environment configuration
variable "environment_name" {
  default = "STAGING"
}

locals {
  env_lower = provider::pyvider::lower(var.environment_name)
  config_file = "config.${local.env_lower}.json"  # "config.staging.json"
}

# Case-insensitive comparison
variable "user_role" {
  default = "Admin"
}

locals {
  is_admin = provider::pyvider::lower(var.user_role) == "admin"
}

# File extension normalization
variable "filename" {
  default = "Document.PDF"
}

locals {
  extension = provider::pyvider::lower(provider::pyvider::split(".", var.filename)[1])  # "pdf"
  is_pdf = local.extension == "pdf"
}
```

## Signature

`lower(text: string) -> string`

## Arguments

- **`text`** (string, required) - The text to convert to lowercase. If `null`, returns `null`.

## Return Value

Returns the input string with all alphabetic characters converted to lowercase:
- **Lowercase string**: All uppercase letters converted to lowercase
- **Non-alphabetic characters**: Remain unchanged
- **Empty string**: Returns `""`
- **Null**: Returns `null` when input is `null`

## Related Functions

- [`upper`](./upper.md) - Convert to uppercase
- [`to_snake_case`](./to_snake_case.md) - Convert to snake_case format
- [`to_camel_case`](./to_camel_case.md) - Convert to camelCase format
- [`contains`](./contains.md) - Case-sensitive string contains
- [`replace`](./replace.md) - Replace text patterns