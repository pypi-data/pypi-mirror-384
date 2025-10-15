---
page_title: "Function: join"
description: |-
  Joins list elements into a string with a specified delimiter
---

# join (Function)

> Combines list elements into a single string using a specified delimiter with null-safe handling

The `join` function takes a delimiter and a list of values, converts each value to a string, and joins them together with the delimiter. It handles null values gracefully and automatically converts non-string values to strings.

## When to Use This

- **Path construction**: Build file paths from path components
- **URL building**: Construct URLs from segments
- **Configuration strings**: Create comma-separated lists or other delimited formats
- **Command building**: Assemble command-line arguments
- **Display formatting**: Format lists for user display

**Anti-patterns (when NOT to use):**
- Complex string templating (use `format` instead)
- Single value formatting (unnecessary overhead)
- Binary data concatenation
- When delimiter conflicts with content

## Quick Start

```terraform
# Simple join with comma
locals {
  items = ["apple", "banana", "cherry"]
  csv_list = provider::pyvider::join(",", local.items)  # Returns: "apple,banana,cherry"
}

# Path construction
locals {
  path_parts = ["var", "log", "myapp"]
  full_path = provider::pyvider::join("/", local.path_parts)  # Returns: "var/log/myapp"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Path Construction

{{ example("path_construction") }}

### Configuration Lists

{{ example("configuration_lists") }}

### Command Building

{{ example("command_building") }}

## Signature

`join(delimiter: string, strings: list[any]) -> string`

## Arguments

- **`delimiter`** (string, required) - The string to use as a separator between elements. Can be empty string for concatenation. Uses empty string if `null`.
- **`strings`** (list[any], required) - A list of values to join. Each value is automatically converted to a string. Returns `null` if the list is `null`.

## Return Value

Returns a string with all list elements joined by the delimiter:
- Each list element is converted to a string using `tostring()`
- Empty lists return an empty string
- Returns `null` if the input list is `null`
- Uses empty string as delimiter if delimiter is `null`

## Common Patterns

### CSV Generation
```terraform
variable "server_names" {
  type = list(string)
  default = ["web1", "web2", "web3"]
}

locals {
  server_list = provider::pyvider::join(",", var.server_names)
}

resource "pyvider_file_content" "server_config" {
  filename = "/tmp/servers.conf"
  content  = "servers=${local.server_list}"
}
```

### Path Building
```terraform
variable "base_path" {
  type = string
  default = "/opt"
}

variable "app_name" {
  type = string
  default = "myapp"
}

locals {
  app_path = provider::pyvider::join("/", [var.base_path, var.app_name, "bin"])
}
```

### Space-Separated Lists
```terraform
variable "tags" {
  type = list(string)
  default = ["web", "production", "frontend"]
}

locals {
  tag_string = provider::pyvider::join(" ", var.tags)
}
```

## Related Functions

- [`split`](./split.md) - Split strings into lists (opposite operation)
- [`format`](./format.md) - Format strings with placeholders
- [`replace`](./replace.md) - Replace text patterns in strings
