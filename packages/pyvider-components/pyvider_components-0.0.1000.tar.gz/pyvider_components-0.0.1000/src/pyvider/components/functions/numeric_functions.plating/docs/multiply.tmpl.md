---
page_title: "Function: multiply"
description: |-
  Multiplies two numbers with intelligent integer conversion and null-safe handling
---

# multiply (Function)

> Performs multiplication of two numeric values with null-safe handling and automatic type optimization

The `multiply` function multiplies two numbers (integers or floats) and returns the result. It handles null values gracefully and automatically converts floating-point results to integers when they represent whole numbers.

## When to Use This

- **Scaling calculations**: Scale values by multipliers or factors
- **Resource sizing**: Calculate total capacity based on unit size
- **Area calculations**: Compute areas, volumes, or dimensions
- **Cost calculations**: Calculate total costs based on unit prices
- **Percentage calculations**: Apply percentage multipliers

**Anti-patterns (when NOT to use):**
- Complex mathematical operations (use multiple function calls)
- String repetition (use appropriate string functions)
- List/array operations (use collection functions)
- Boolean logic (use conditional expressions)

## Quick Start

```terraform
# Simple multiplication
locals {
  total_storage = provider::pyvider::multiply(10, 5)  # Returns: 50
}

# Scaling with variables
variable "instances" {
  default = 4
}

variable "cpu_per_instance" {
  default = 2
}

locals {
  total_cpu = provider::pyvider::multiply(var.instances, var.cpu_per_instance)  # Returns: 8
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Resource Scaling

{{ example("resource_calculations") }}

### Cost Calculations

```terraform
# Simple cost multiplication
variable "unit_price" {
  type = number
  default = 12.50
}

variable "quantity" {
  type = number
  default = 8
}

locals {
  total_cost = provider::pyvider::multiply(var.unit_price, var.quantity)  # 100.0
}

# Percentage calculations
locals {
  base_price = 1000
  tax_rate = 0.08
  total_with_tax = provider::pyvider::multiply(local.base_price, provider::pyvider::add(1, local.tax_rate))  # 1080
}
```

## Signature

`multiply(a: number, b: number) -> number`

## Arguments

- **`a`** (number, required) - The first number to multiply. Can be an integer or float. Returns `null` if this value is `null`.
- **`b`** (number, required) - The second number to multiply. Can be an integer or float. Returns `null` if this value is `null`.

## Return Value

Returns the product of `a` and `b` as a number. The return type is automatically optimized:
- If the result is a whole number (e.g., `6.0`), returns an integer (`6`)
- If the result has decimal places (e.g., `6.75`), returns a float (`6.75`)
- Returns `null` if either input is `null`

## Common Patterns

### Resource Capacity
```terraform
variable "nodes" {
  type    = number
  default = 3
}

variable "cores_per_node" {
  type    = number
  default = 8
}

locals {
  total_cores = provider::pyvider::multiply(var.nodes, var.cores_per_node)
}

resource "pyvider_file_content" "capacity_report" {
  filename = "/tmp/capacity.txt"
  content  = "Total CPU cores: ${local.total_cores}"
}
```

### Cost Estimation
```terraform
variable "unit_price" {
  type = number
}

variable "quantity" {
  type = number
}

locals {
  total_cost = provider::pyvider::multiply(var.unit_price, var.quantity)
}
```

## Related Functions

- [`add`](./add.md) - Add two numbers
- [`subtract`](./subtract.md) - Subtract two numbers
- [`divide`](./divide.md) - Divide two numbers
- [`round`](./round.md) - Round the result to specific precision
