---
page_title: "Function: split"
description: |-
  Splits a string into a list using a specified delimiter
---

# split (Function)

> Divides a string into a list of substrings using a specified delimiter with null-safe handling

The `split` function takes a delimiter and a string, then returns a list of substrings created by splitting the original string at each occurrence of the delimiter. It handles null values gracefully and edge cases like empty strings.

## When to Use This

- **Path parsing**: Split file paths into components
- **CSV processing**: Parse comma-separated values
- **Configuration parsing**: Split delimited configuration strings
- **Tag processing**: Split tag strings into individual tags
- **Data extraction**: Extract values from structured strings

**Anti-patterns (when NOT to use):**
- Complex parsing (use proper parsers for JSON, XML, etc.)
- Single character extraction (use string indexing)
- Binary data splitting
- When delimiter doesn't exist in string (returns single-element list)

## Quick Start

```terraform
# Simple CSV splitting
locals {
  csv_data = "apple,banana,cherry"
  fruits = provider::pyvider::split(",", local.csv_data)  # Returns: ["apple", "banana", "cherry"]
}

# Path splitting
locals {
  file_path = "/var/log/myapp/error.log"
  path_parts = provider::pyvider::split("/", local.file_path)  # Returns: ["", "var", "log", "myapp", "error.log"]
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Path Processing

{{ example("path_processing") }}

### Configuration Parsing

{{ example("configuration_parsing") }}

### Tag Processing

{{ example("tag_processing") }}

## Signature

`split(delimiter: string, string: string) -> list[string]`

## Arguments

- **`delimiter`** (string, required) - The string to split on. Uses empty string if `null` (splits into individual characters).
- **`string`** (string, required) - The string to split. Returns `null` if this value is `null`.

## Return Value

Returns a list of strings created by splitting the input:
- Empty string returns an empty list `[]`
- String without delimiter returns a single-element list `["original_string"]`
- Returns `null` if the input string is `null`
- Empty delimiter splits into individual characters

## Behavior Details

### Empty String Handling
```terraform
locals {
  empty_result = provider::pyvider::split(",", "")  # Returns: []
  single_item = provider::pyvider::split(",", "single")  # Returns: ["single"]
}
```

### Leading/Trailing Delimiters
```terraform
locals {
  leading = provider::pyvider::split(",", ",apple,banana")  # Returns: ["", "apple", "banana"]
  trailing = provider::pyvider::split(",", "apple,banana,")  # Returns: ["apple", "banana", ""]
}
```

## Common Patterns

### Environment Variable Processing
```terraform
variable "path_env" {
  type = string
  default = "/usr/bin:/usr/local/bin:/opt/bin"
}

locals {
  path_directories = provider::pyvider::split(":", var.path_env)
}

resource "pyvider_file_content" "path_config" {
  filename = "/tmp/paths.txt"
  content = join("\n", [
    "Available paths:",
    for path in local.path_directories : "- ${path}"
  ])
}
```

### Configuration List Processing
```terraform
variable "allowed_hosts" {
  type = string
  default = "web1.example.com,web2.example.com,api.example.com"
}

locals {
  host_list = provider::pyvider::split(",", var.allowed_hosts)
}
```

### Filename Extension Extraction
```terraform
variable "filename" {
  type = string
  default = "document.backup.pdf"
}

locals {
  filename_parts = provider::pyvider::split(".", var.filename)
  file_extension = length(local.filename_parts) > 1 ? local.filename_parts[length(local.filename_parts) - 1] : ""
}
```

## Best Practices

### 1. Validate Input
```terraform
variable "csv_input" {
  type = string
  validation {
    condition     = length(var.csv_input) > 0
    error_message = "Input cannot be empty."
  }
}

locals {
  csv_items = provider::pyvider::split(",", var.csv_input)
}
```

### 2. Handle Edge Cases
```terraform
locals {
  safe_split = var.input_string != null && var.input_string != "" ? provider::pyvider::split(",", var.input_string) : []
}
```

## Related Functions

- [`join`](./join.md) - Join lists into strings (opposite operation)
- [`replace`](./replace.md) - Replace text patterns before splitting
- [`format`](./format.md) - Format strings with placeholders
