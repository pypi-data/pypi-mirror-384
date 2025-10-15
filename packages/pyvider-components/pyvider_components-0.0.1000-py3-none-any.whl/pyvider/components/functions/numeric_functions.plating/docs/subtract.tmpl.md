---
page_title: "Function: subtract"
description: |-
  Subtracts one number from another with intelligent integer conversion
---

# subtract (Function)

> Performs subtraction of two numeric values with null-safe handling and automatic type optimization

The `subtract` function subtracts the second number from the first number and returns the result. It handles null values gracefully and automatically converts floating-point results to integers when they represent whole numbers.

## When to Use This

- **Difference calculations**: Calculate differences between values
- **Remaining capacity**: Determine available resources after usage
- **Countdown operations**: Calculate time or quantity remaining
- **Budget analysis**: Calculate remaining budget or overspend
- **Resource depletion**: Track consumption and availability

**Anti-patterns (when NOT to use):**
- Complex mathematical operations (use multiple function calls)
- String operations (use string functions)
- List/array operations (use collection functions)

## Quick Start

```terraform
# Simple subtraction
locals {
  remaining = provider::pyvider::subtract(100, 35)  # Returns: 65
}

# Resource availability
variable "total_capacity" {
  default = 500
}

variable "current_usage" {
  default = 187
}

locals {
  available = provider::pyvider::subtract(var.total_capacity, var.current_usage)  # Returns: 313
}
```

## Examples

{{ example("basic") }}

### Common Use Cases

```terraform
# Budget tracking
variable "budget" {
  type = number
  default = 10000
}

variable "spent" {
  type = number
  default = 3750.50
}

locals {
  remaining_budget = provider::pyvider::subtract(var.budget, var.spent)  # 6249.50
  is_overbudget = local.remaining_budget < 0
}

# Resource capacity management
locals {
  total_memory_gb = 128
  used_memory_gb = 95.5

  free_memory = provider::pyvider::subtract(local.total_memory_gb, local.used_memory_gb)  # 32.5
  memory_percentage_free = provider::pyvider::multiply(
    provider::pyvider::divide(local.free_memory, local.total_memory_gb),
    100
  )
}
```

## Signature

`subtract(a: number, b: number) -> number`

## Arguments

- **`a`** (number, required) - The number to subtract from (minuend). Can be an integer or float. Returns `null` if this value is `null`.
- **`b`** (number, required) - The number to subtract (subtrahend). Can be an integer or float. Returns `null` if this value is `null`.

## Return Value

Returns the difference of `a - b` as a number. The return type is automatically optimized:
- If the result is a whole number (e.g., `5.0`), returns an integer (`5`)
- If the result has decimal places (e.g., `5.75`), returns a float (`5.75`)
- Returns `null` if either input is `null`
- Can return negative numbers when `b > a`

## Related Functions

- [`add`](./add.md) - Add two numbers
- [`multiply`](./multiply.md) - Multiply two numbers
- [`divide`](./divide.md) - Divide two numbers
- [`sum`](./sum.md) - Sum a list of numbers