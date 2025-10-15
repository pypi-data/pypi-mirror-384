---
page_title: "Data Source: pyvider_lens_jq"
description: |-
  Transforms JSON data using JQ queries with powerful filtering and manipulation
---

# pyvider_lens_jq (Data Source)

> Transform and query JSON data using the powerful JQ language

The `pyvider_lens_jq` data source allows you to transform JSON data using JQ queries. This enables complex data manipulation, filtering, and extraction from JSON sources such as API responses, configuration files, or structured data within your Terraform configurations.

## When to Use This

- **JSON data transformation**: Process complex JSON structures from APIs or files
- **Data extraction**: Pull specific values from nested JSON documents
- **Configuration processing**: Transform configuration formats between systems
- **API response filtering**: Extract relevant data from large API responses
- **Data validation**: Check JSON structure and validate required fields

**Anti-patterns (when NOT to use):**
- Simple field access (use direct Terraform syntax instead)
- Non-JSON data (use string manipulation functions)
- Very large datasets (consider performance implications)
- Real-time data processing (this is for configuration-time transformation)

## Quick Start

```terraform
# Transform JSON configuration data
data "pyvider_lens_jq" "config_transform" {
  json_input = jsonencode({
    users = [
      { name = "Alice", role = "admin", active = true },
      { name = "Bob", role = "user", active = false }
    ]
  })
  query = ".users | map(select(.active)) | map(.name)"
}

# Result will be ["Alice"]
output "active_users" {
  value = data.pyvider_lens_jq.config_transform.result
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Complex Transformations

{{ example("complex") }}

### API Response Processing

{{ example("api_processing") }}

## Schema

{{ schema() }}

## JQ Query Language

The data source uses the JQ query language for JSON processing. Here are key patterns:

### Basic Operations
- **`.field`** - Extract a field
- **`.nested.field`** - Extract nested field
- **`.[0]`** - Get first array element
- **`.[]`** - Iterate over array/object values

### Array Operations
- **`map(expression)`** - Transform each array element
- **`select(condition)`** - Filter elements
- **`length`** - Get array/object length
- **`sort_by(.field)`** - Sort by field value

### Filtering and Conditions
- **`select(.field == "value")`** - Filter by exact match
- **`select(.field > 10)`** - Numeric comparisons
- **`select(.field | test("pattern"))`** - Regex matching

### Data Manipulation
- **`{new_key: .old_key}`** - Reshape objects
- **`add`** - Sum array of numbers
- **`group_by(.field)`** - Group elements
- **`unique`** - Remove duplicates

## Common Patterns

### Extract Specific Fields
```terraform
data "pyvider_lens_jq" "extract_names" {
  json_input = jsonencode(var.users)
  query = ".[] | .name"
}
```

### Filter and Transform
```terraform
data "pyvider_lens_jq" "active_admins" {
  json_input = jsonencode(var.users)
  query = ".[] | select(.active and .role == \"admin\") | {name, email}"
}
```

### Statistical Operations
```terraform
data "pyvider_lens_jq" "user_stats" {
  json_input = jsonencode(var.users)
  query = "{total: length, active: [.[] | select(.active)] | length}"
}
```

### Complex Nested Processing
```terraform
data "pyvider_lens_jq" "department_summary" {
  json_input = jsonencode(var.company_data)
  query = ".departments | map({
    name: .name,
    employee_count: .employees | length,
    avg_salary: (.employees | map(.salary) | add / length)
  })"
}
```

## Integration with HTTP APIs

Transform API responses for use in Terraform:

```terraform
# Fetch data from API
data "pyvider_http_api" "github_repos" {
  url = "https://api.github.com/users/octocat/repos"
}

# Transform the response
data "pyvider_lens_jq" "repo_summary" {
  json_input = data.pyvider_http_api.github_repos.response_body
  query = "map(select(.private == false)) | map({
    name: .name,
    language: .language,
    stars: .stargazers_count
  }) | sort_by(.stars) | reverse"
}
```

## Configuration Management

Process environment-specific configurations:

```terraform
# Read environment variables
data "pyvider_env_variables" "config" {
  prefix = "APP_"
}

# Transform to application config format
data "pyvider_lens_jq" "app_config" {
  json_input = jsonencode(data.pyvider_env_variables.config.values)
  query = "to_entries | map({
    key: (.key | sub(\"APP_\"; \"\") | ascii_downcase),
    value: .value
  }) | from_entries"
}
```

## Error Handling

Handle malformed JSON or failed queries:

```terraform
data "pyvider_lens_jq" "safe_transform" {
  json_input = var.json_data
  query = "try (.users | map(.name)) catch []"
}

# Check if transformation succeeded
locals {
  transform_success = data.pyvider_lens_jq.safe_transform.result != null
  user_count = local.transform_success ? length(data.pyvider_lens_jq.safe_transform.result) : 0
}
```

## Performance Considerations

1. **Data Size**: JQ is efficient but very large JSON documents may impact performance
2. **Query Complexity**: Complex nested operations are slower than simple extractions
3. **Caching**: Results are cached during Terraform runs
4. **Memory Usage**: Large transformations may use significant memory

## Advanced JQ Patterns

### Grouping and Aggregation
```jq
group_by(.department) | map({
  department: .[0].department,
  count: length,
  avg_salary: (map(.salary) | add / length)
})
```

### Conditional Transformations
```jq
map(if .active then {name, role} else {name, status: "inactive"} end)
```

### Date Processing
```jq
map(.created_at | strptime("%Y-%m-%d") | strftime("%m/%d/%Y"))
```

### Deep Merging
```jq
reduce .[] as $item ({}; . * $item)
```

## Debugging JQ Queries

1. **Start Simple**: Begin with basic field extraction
2. **Use `debug` operator**: Add `| debug` to see intermediate values
3. **Test Incrementally**: Build complex queries step by step
4. **Online JQ Playground**: Test queries at jqplay.org before using

## Common Issues & Solutions

### Error: "Invalid JSON input"
**Solution**: Ensure `json_input` contains valid JSON string

```terraform
# ❌ Wrong - passing object directly
data "pyvider_lens_jq" "wrong" {
  json_input = var.my_object  # This is an object, not JSON
  query = ".field"
}

# ✅ Correct - encode to JSON first
data "pyvider_lens_jq" "correct" {
  json_input = jsonencode(var.my_object)
  query = ".field"
}
```

### Error: "JQ query failed"
**Solution**: Use `try-catch` for optional operations

```terraform
data "pyvider_lens_jq" "safe" {
  json_input = jsonencode(var.data)
  query = "try .optional_field catch null"
}
```

### Empty Results
**Solution**: Check your filter conditions and data structure

```terraform
# Debug what's in your data
data "pyvider_lens_jq" "debug" {
  json_input = jsonencode(var.data)
  query = "keys"  # Shows top-level keys
}
```

## Related Components

- [`lens_jq` function](../../functions/lens_jq.md) - Use JQ transformations in function calls
- [`pyvider_http_api`](../http_api.md) - Fetch JSON data from APIs for transformation
- [`pyvider_file_content`](../../resources/file_content.md) - Write transformed JSON to files
- [`pyvider_env_variables`](../env_variables.md) - Transform environment variable data