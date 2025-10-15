---
page_title: "Function: lens_jq"
description: |-
  Applies jq queries to JSON data for powerful data transformation and extraction
---

# lens_jq (Function)

> Applies jq queries to JSON data and returns transformed results as native objects

The `lens_jq` function enables powerful JSON data transformation using jq query syntax. It applies jq expressions to input data and returns the results as native Terraform objects, making it ideal for complex data manipulation and extraction tasks.

## When to Use This

- **JSON data transformation**: Transform complex JSON structures
- **API response processing**: Extract specific fields from API responses
- **Configuration manipulation**: Modify or extract configuration data
- **Data filtering**: Filter arrays and objects based on criteria
- **Complex data extraction**: Perform advanced queries on nested data

**Anti-patterns (when NOT to use):**
- Simple key access (use direct object access)
- Performance-critical paths (jq has overhead)
- When simpler functions suffice
- Non-JSON data types

## Quick Start

```terraform
# Extract specific field
locals {
  data = {
    users = [
      { name = "Alice", age = 30 },
      { name = "Bob", age = 25 }
    ]
  }
  names = provider::pyvider::lens_jq(".users[].name", local.data)  # Returns: ["Alice", "Bob"]
}

# Filter data
locals {
  filtered_users = provider::pyvider::lens_jq(".users[] | select(.age > 27)", local.data)
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Data Transformation

{{ example("data_transformation") }}

### API Response Processing

{{ example("api_response_processing") }}

### Complex Queries

{{ example("complex_queries") }}

## Signature

`lens_jq(query: string, data: any) -> any`

## Arguments

- **`query`** (string, required) - The jq expression to apply to the data
- **`data`** (any, required) - The input data to query (typically JSON-like objects)

## Return Value

Returns the result of applying the jq query to the input data. The return type depends on the query:
- Objects, arrays, strings, numbers, or booleans based on the query result
- `null` if the query returns null or if input data is null

## Common jq Query Patterns

### Field Extraction
```terraform
locals {
  config = { database = { host = "localhost", port = 5432 } }
  host = provider::pyvider::lens_jq(".database.host", local.config)  # "localhost"
  port = provider::pyvider::lens_jq(".database.port", local.config)  # 5432
}
```

### Array Processing
```terraform
locals {
  servers = {
    instances = [
      { name = "web-1", status = "running" },
      { name = "web-2", status = "stopped" },
      { name = "db-1", status = "running" }
    ]
  }

  running_servers = provider::pyvider::lens_jq(
    ".instances[] | select(.status == \"running\") | .name",
    local.servers
  )  # ["web-1", "db-1"]
}
```

### Data Transformation
```terraform
locals {
  raw_data = {
    metrics = [
      { service = "api", cpu = 75, memory = 60 },
      { service = "db", cpu = 45, memory = 80 }
    ]
  }

  transformed = provider::pyvider::lens_jq(
    ".metrics | map({name: .service, load: (.cpu + .memory) / 2})",
    local.raw_data
  )  # [{"name": "api", "load": 67.5}, {"name": "db", "load": 62.5}]
}
```

## Related Functions

- [`lookup`](../collection_functions/lookup.md) - Simple key-value lookups
- [`contains`](../collection_functions/contains.md) - Check array membership
- [`length`](../collection_functions/length.md) - Get collection sizes
