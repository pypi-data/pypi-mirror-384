---
page_title: "Data Source: nested_data_test_suite"
description: |-
  Processes and validates complex nested data structures for Terraform provider testing
---

# nested_data_test_suite (Data Source)

> Processes complex nested data structures for testing CTY data handling and validation

The `pyvider_nested_data_processor` data source is designed for testing and validating complex nested data structures within Terraform providers. It processes nested objects, maps, and lists to ensure proper CTY (Cloud Terraform YAML) data type handling and serialization.

## When to Use This

- **Provider testing**: Test complex data structure handling in Terraform providers
- **Data validation**: Validate nested data structures before processing
- **CTY testing**: Test CTY data type conversion and serialization
- **Development workflows**: Debug complex data structures during provider development
- **Integration testing**: Test data flow through provider components

**Anti-patterns (when NOT to use):**
- Production workloads (this is a testing/development tool)
- Simple data structures (use standard data sources)
- Performance-critical applications
- When data validation is not needed

## Quick Start

```terraform
# Test nested data processing
data "pyvider_nested_data_processor" "test" {
  input_data = {
    level1 = {
      level2 = {
        values = ["a", "b", "c"]
        count = 3
      }
    }
  }
}

# Access processed results
output "processed_data" {
  value = data.pyvider_nested_data_processor.test.processed_data
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Complex Nested Structures

{{ example("complex_nested") }}

### Data Validation Testing

{{ example("data_validation") }}

### CTY Type Testing

{{ example("cty_type_testing") }}

## Schema

{{ schema() }}

## Common Patterns

### Testing Provider Data Flow
```terraform
# Test complex configuration data
data "pyvider_nested_data_processor" "config_test" {
  input_data = {
    database = {
      connections = [
        {
          host = "primary.db.example.com"
          port = 5432
          ssl_config = {
            enabled = true
            cert_path = "/etc/ssl/certs/db.pem"
          }
        },
        {
          host = "replica.db.example.com"
          port = 5432
          ssl_config = {
            enabled = false
            cert_path = null
          }
        }
      ]
    }
  }
}

# Verify processing results
resource "pyvider_file_content" "test_results" {
  filename = "/tmp/nested_data_test.json"
  content  = jsonencode(data.pyvider_nested_data_processor.config_test.processed_data)
}
```

### Validation Testing
```terraform
# Test data structure validation
data "pyvider_nested_data_processor" "validation_test" {
  input_data = {
    users = [
      {
        name = "alice"
        permissions = {
          read = true
          write = true
          admin = false
        }
        metadata = {
          created_at = "2023-01-01T00:00:00Z"
          tags = ["developer", "team-lead"]
        }
      }
    ]
  }
}
```

## Best Practices

### 1. Use for Development and Testing Only
```terraform
# Good - clearly marked as testing
data "pyvider_nested_data_processor" "dev_test" {
  input_data = var.test_data_structure
}
```

### 2. Structure Test Data Clearly
```terraform
variable "test_nested_data" {
  description = "Test data for nested structure validation"
  type = object({
    config = map(any)
    metadata = object({
      version = string
      tags = list(string)
    })
  })
}

data "pyvider_nested_data_processor" "structured_test" {
  input_data = var.test_nested_data
}
```

### 3. Validate Processing Results
```terraform
# Check that processing completed successfully
locals {
  processing_successful = data.pyvider_nested_data_processor.test.data_hash != null
}

resource "pyvider_file_content" "test_status" {
  count = local.processing_successful ? 1 : 0
  filename = "/tmp/test_passed.txt"
  content  = "Nested data processing test passed"
}
```

## Related Components

- [`pyvider_file_content`](../../resources/file_content.md) - Write test results to files
- [`pyvider_env_variables`](../env_variables.md) - Access environment data for testing
- [`lens_jq` function](../../functions/lens_jq.md) - Query and transform nested data
