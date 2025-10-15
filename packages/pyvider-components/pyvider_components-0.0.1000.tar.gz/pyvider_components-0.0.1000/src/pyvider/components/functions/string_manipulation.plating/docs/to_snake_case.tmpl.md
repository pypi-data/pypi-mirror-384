---
page_title: "Function: to_snake_case"
description: |-
  Converts text to snake_case format with intelligent word separation
---

# to_snake_case (Function)

> Converts text to snake_case format by replacing spaces and other separators with underscores

The `to_snake_case` function converts text to snake_case format, which uses lowercase letters with underscores separating words. It intelligently handles various input formats including camelCase, PascalCase, kebab-case, and space-separated text.

## When to Use This

- **Variable naming**: Convert user input to valid Python/Terraform variable names
- **File naming**: Create consistent snake_case filenames from titles
- **Database columns**: Standardize column names in snake_case format
- **API endpoints**: Convert display names to API-friendly snake_case paths
- **Configuration keys**: Normalize configuration keys to snake_case

**Anti-patterns (when NOT to use):**
- When preserving original case is important
- For display text that should remain readable
- When working with external APIs that expect specific casing

## Quick Start

```terraform
# Convert display text to snake_case
locals {
  page_title = "User Profile Settings"
  snake_name = provider::pyvider::to_snake_case(local.page_title)  # Returns: "user_profile_settings"
}

# Convert camelCase to snake_case
variable "apiEndpointName" {
  default = "getUserData"
}

locals {
  endpoint_snake = provider::pyvider::to_snake_case(var.apiEndpointName)  # Returns: "get_user_data"
}
```

## Examples

{{ example("basic") }}

### Common Use Cases

```terraform
# Database column naming
locals {
  user_fields = ["First Name", "Email Address", "Phone Number"]

  db_columns = [
    for field in local.user_fields :
    provider::pyvider::to_snake_case(field)
  ]
  # Result: ["first_name", "email_address", "phone_number"]
}

# File naming from titles
variable "document_title" {
  default = "Quarterly Sales Report 2024"
}

locals {
  filename = "${provider::pyvider::to_snake_case(var.document_title)}.pdf"  # "quarterly_sales_report_2024.pdf"
}
```

## Signature

`to_snake_case(text: string) -> string`

## Arguments

- **`text`** (string, required) - The text to convert to snake_case. Handles various input formats:
  - `camelCase` (userName)
  - `PascalCase` (UserName)
  - `kebab-case` (user-name)
  - `space separated` (user name)
  - `Mixed-Format_text` (mixed separators)
  - If `null`, returns `null`

## Return Value

Returns the converted string in snake_case format:
- **snake_case**: All lowercase with underscores separating words → `user_profile_data`
- **Empty string**: Returns `""` when input is empty
- **Null**: Returns `null` when input is `null`

## Processing Rules

The function applies these transformations:
1. **Convert to lowercase**: All characters converted to lowercase
2. **Replace separators**: Hyphens (`-`), spaces (` `), and existing underscores remain as underscores
3. **Word boundaries**: CamelCase and PascalCase word boundaries become underscores
4. **Clean up**: Multiple consecutive separators become single underscores
5. **Trim**: Leading and trailing separators are removed

## Related Functions

- [`to_camel_case`](./to_camel_case.md) - Convert to camelCase format
- [`to_kebab_case`](./to_kebab_case.md) - Convert to kebab-case format
- [`upper`](./upper.md) - Convert to uppercase
- [`lower`](./lower.md) - Convert to lowercase
- [`replace`](./replace.md) - Replace specific text patterns