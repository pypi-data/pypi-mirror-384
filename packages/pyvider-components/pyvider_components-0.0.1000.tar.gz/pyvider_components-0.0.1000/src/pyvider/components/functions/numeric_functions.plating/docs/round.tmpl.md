---
page_title: "Function: round"
description: |-
  Rounds a number to a specified decimal precision with null-safe handling
---

# round (Function)

> Rounds a numeric value to a specified number of decimal places with null-safe handling

The `round` function rounds a number to a specified precision (number of decimal places). It handles null values gracefully and defaults to rounding to the nearest integer when no precision is specified.

## When to Use This

- **Display formatting**: Round numbers for user-friendly display
- **Currency calculations**: Round monetary values to appropriate precision
- **Percentage calculations**: Round percentages to desired decimal places
- **Measurement precision**: Round measurements to appropriate accuracy
- **Performance metrics**: Round metrics for cleaner reporting

**Anti-patterns (when NOT to use):**
- Financial calculations requiring exact precision (use appropriate decimal libraries)
- When exact floating-point values are critical
- Integer-only operations (unnecessary overhead)

## Quick Start

```terraform
# Round to nearest integer
locals {
  price = 19.847
  rounded_price = provider::pyvider::round(local.price, 0)  # Returns: 20
}

# Round to 2 decimal places (currency)
locals {
  calculation_result = 123.456789
  currency_amount = provider::pyvider::round(local.calculation_result, 2)  # Returns: 123.46
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Currency Formatting

{{ example("currency_formatting") }}

### Percentage Calculations

{{ example("percentage_calculations") }}

### Measurement Precision

{{ example("measurement_precision") }}

## Signature

`round(number: number, precision?: number) -> number`

## Arguments

- **`number`** (number, required) - The number to round. Can be an integer or float. Returns `null` if this value is `null`.
- **`precision`** (number, optional) - The number of decimal places to round to. Defaults to `0` (round to nearest integer). Returns `null` if this value is `null`.

## Return Value

Returns the rounded number:
- When `precision` is `0`: returns an integer
- When `precision` is positive: returns a float with the specified decimal places
- Returns `null` if either input is `null`

## Common Patterns

### Currency Rounding
```terraform
variable "item_costs" {
  type = list(number)
  default = [12.456, 8.923, 15.789]
}

locals {
  total_cost = provider::pyvider::sum(var.item_costs)
  rounded_total = provider::pyvider::round(local.total_cost, 2)
}

resource "pyvider_file_content" "invoice" {
  filename = "/tmp/invoice.txt"
  content  = "Total: $${local.rounded_total}"
}
```

### Percentage Display
```terraform
variable "completed_tasks" {
  type = number
}

variable "total_tasks" {
  type = number
}

locals {
  raw_percentage = provider::pyvider::multiply(
    provider::pyvider::divide(var.completed_tasks, var.total_tasks),
    100
  )
  display_percentage = provider::pyvider::round(local.raw_percentage, 1)
}
```

### Measurement Precision
```terraform
locals {
  precise_measurement = 2.718281828
  engineering_precision = provider::pyvider::round(local.precise_measurement, 3)  # 2.718
  display_precision = provider::pyvider::round(local.precise_measurement, 1)      # 2.7
}
```

## Best Practices

### 1. Choose Appropriate Precision
```terraform
locals {
  # Currency: 2 decimal places
  price = provider::pyvider::round(var.raw_price, 2)

  # Percentages: 1-2 decimal places
  percentage = provider::pyvider::round(var.raw_percentage, 1)

  # Display metrics: 0-1 decimal places
  metric = provider::pyvider::round(var.raw_metric, 0)
}
```

### 2. Handle Null Values
```terraform
locals {
  safe_rounded = var.optional_value != null ? provider::pyvider::round(var.optional_value, 2) : null
}
```

## Related Functions

- [`add`](./add.md) - Add numbers (often rounded afterward)
- [`subtract`](./subtract.md) - Subtract numbers (often rounded afterward)
- [`multiply`](./multiply.md) - Multiply numbers (often rounded afterward)
- [`divide`](./divide.md) - Divide numbers (often rounded afterward)
