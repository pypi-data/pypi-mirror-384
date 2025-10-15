---
page_title: "Function: add"
description: |-
  Adds two numbers and returns the result with intelligent integer conversion
---

# add (Function)

> Performs addition of two numeric values with null-safe handling and automatic type optimization

The `add` function adds two numbers (integers or floats) and returns the result. It handles null values gracefully and automatically converts floating-point results to integers when they represent whole numbers.

## When to Use This

- **Arithmetic calculations**: Perform basic addition in Terraform configurations
- **Counter increments**: Add values to existing counters or indices
- **Resource calculations**: Compute resource counts or sizing values
- **Configuration math**: Calculate derived configuration values
- **Budget calculations**: Sum costs or allocations

**Anti-patterns (when NOT to use):**
- Complex mathematical operations (use multiple function calls)
- String concatenation (use `join` or template interpolation)
- List/array operations (use collection functions)
- Boolean logic (use conditional expressions)

## Quick Start

```terraform
# Simple addition
locals {
  total_servers = provider::pyvider::add(3, 5)  # Returns: 8
}

# Adding with variables
variable "base_count" {
  default = 10
}

variable "additional_count" {
  default = 5
}

locals {
  final_count = provider::pyvider::add(var.base_count, var.additional_count)  # Returns: 15
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Resource Calculations

{{ example("resource_calculations") }}

### Configuration Math

{{ example("configuration_math") }}

### Null Handling

{{ example("null_handling") }}

## Signature

`add(a: number, b: number) -> number`

## Arguments

- **`a`** (number, required) - The first number to add. Can be an integer or float. Returns `null` if this value is `null`.
- **`b`** (number, required) - The second number to add. Can be an integer or float. Returns `null` if this value is `null`.

## Return Value

Returns the sum of `a` and `b` as a number. The return type is automatically optimized:
- If the result is a whole number (e.g., `5.0`), returns an integer (`5`)
- If the result has decimal places (e.g., `5.7`), returns a float (`5.7`)
- Returns `null` if either input is `null`

## Behavior Details

### Null Safety
```terraform
locals {
  # These all return null
  result1 = provider::pyvider::add(null, 5)     # null
  result2 = provider::pyvider::add(3, null)     # null
  result3 = provider::pyvider::add(null, null)  # null
}
```

### Type Optimization
```terraform
locals {
  # Integer results when possible
  int_result = provider::pyvider::add(3, 7)      # 10 (integer)
  int_from_float = provider::pyvider::add(3.0, 7.0)  # 10 (integer, not 10.0)

  # Float results when necessary
  float_result = provider::pyvider::add(3.5, 2.1)    # 5.6 (float)
  mixed_result = provider::pyvider::add(3, 2.5)      # 5.5 (float)
}
```

### Precision Considerations
```terraform
locals {
  # Be aware of floating-point precision
  precise_calc = provider::pyvider::add(0.1, 0.2)  # May be 0.30000000000000004

  # Use round() for display if needed
  rounded_result = provider::pyvider::round(
    provider::pyvider::add(0.1, 0.2),
    2
  )  # 0.30
}
```

## Common Patterns

### Counter Increments
```terraform
variable "current_index" {
  type    = number
  default = 0
}

locals {
  next_index = provider::pyvider::add(var.current_index, 1)
}

resource "pyvider_file_content" "indexed_file" {
  filename = "/tmp/file_${local.next_index}.txt"
  content  = "This is file number ${local.next_index}"
}
```

### Resource Scaling
```terraform
variable "base_instances" {
  type    = number
  default = 2
}

variable "additional_instances" {
  type    = number
  default = 3
}

locals {
  total_instances = provider::pyvider::add(var.base_instances, var.additional_instances)
}

# Use in resource count
resource "pyvider_local_directory" "instance_dirs" {
  count = local.total_instances
  path  = "/tmp/instance_${count.index + 1}"
}
```

### Budget Calculations
```terraform
variable "base_cost" {
  type = number
}

variable "additional_features_cost" {
  type = number
}

locals {
  total_budget = provider::pyvider::add(var.base_cost, var.additional_features_cost)
}

resource "pyvider_file_content" "budget_report" {
  filename = "/tmp/budget.txt"
  content = join("\n", [
    "Budget Calculation:",
    "Base Cost: $${var.base_cost}",
    "Additional Features: $${var.additional_features_cost}",
    "Total Budget: $${local.total_budget}"
  ])
}
```

## Error Handling

### Type Errors
```terraform
# These will cause errors at runtime
locals {
  # Error: Cannot add string and number
  # bad_result = provider::pyvider::add("hello", 5)

  # Error: Cannot add boolean and number
  # bad_result2 = provider::pyvider::add(true, 3)
}
```

### Handling Invalid Inputs
```terraform
variable "user_input_a" {
  type = any
}

variable "user_input_b" {
  type = any
}

locals {
  # Safely convert to numbers first
  safe_a = try(tonumber(var.user_input_a), 0)
  safe_b = try(tonumber(var.user_input_b), 0)

  safe_result = provider::pyvider::add(local.safe_a, local.safe_b)
}
```

## Performance Considerations

- **Lightweight operation**: Addition is extremely fast and has minimal overhead
- **Memory efficient**: No memory allocation for the calculation itself
- **Type conversion**: Minimal overhead for integer optimization
- **Null checking**: Fast null validation before calculation

## Best Practices

### 1. Input Validation
```terraform
variable "count_a" {
  type = number
  validation {
    condition     = var.count_a >= 0
    error_message = "Count must be non-negative."
  }
}

variable "count_b" {
  type = number
  validation {
    condition     = var.count_b >= 0
    error_message = "Count must be non-negative."
  }
}

locals {
  total_count = provider::pyvider::add(var.count_a, var.count_b)
}
```

### 2. Null-Safe Calculations
```terraform
# Provide defaults for potentially null values
locals {
  safe_total = provider::pyvider::add(
    coalesce(var.optional_value_a, 0),
    coalesce(var.optional_value_b, 0)
  )
}
```

### 3. Complex Calculations
```terraform
# Break down complex calculations
locals {
  subtotal_1 = provider::pyvider::add(var.base_cost, var.feature_cost)
  subtotal_2 = provider::pyvider::add(var.license_cost, var.support_cost)
  grand_total = provider::pyvider::add(local.subtotal_1, local.subtotal_2)
}
```

## Related Functions

- [`subtract`](./subtract.md) - Subtract two numbers
- [`multiply`](./multiply.md) - Multiply two numbers
- [`divide`](./divide.md) - Divide two numbers
- [`sum`](./sum.md) - Add multiple numbers from a list
- [`round`](./round.md) - Round the result to specific precision
