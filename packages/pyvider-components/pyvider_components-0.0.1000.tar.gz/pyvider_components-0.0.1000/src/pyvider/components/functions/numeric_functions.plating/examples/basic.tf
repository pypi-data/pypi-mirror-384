# Basic numeric function examples

# Addition examples
locals {
  simple_add = provider::pyvider::add(5, 3)      # Returns: 8
  float_add = provider::pyvider::add(2.5, 1.5)   # Returns: 4
  mixed_add = provider::pyvider::add(10, 2.3)    # Returns: 12.3
}

# Subtraction examples
locals {
  simple_subtract = provider::pyvider::subtract(10, 4)    # Returns: 6
  float_subtract = provider::pyvider::subtract(5.5, 2.1)  # Returns: 3.4
  negative_result = provider::pyvider::subtract(3, 7)     # Returns: -4
}

# Multiplication examples
locals {
  simple_multiply = provider::pyvider::multiply(4, 3)     # Returns: 12
  float_multiply = provider::pyvider::multiply(2.5, 4)    # Returns: 10
  zero_multiply = provider::pyvider::multiply(5, 0)       # Returns: 0
}

# Division examples
locals {
  simple_divide = provider::pyvider::divide(12, 3)        # Returns: 4
  float_divide = provider::pyvider::divide(10, 3)         # Returns: 3.333...
  precise_divide = provider::pyvider::divide(15, 3)       # Returns: 5
}

# List operations
locals {
  numbers = [10, 5, 8, 2, 15]

  list_sum = provider::pyvider::sum(local.numbers)         # Returns: 40
  list_min = provider::pyvider::min(local.numbers)         # Returns: 2
  list_max = provider::pyvider::max(local.numbers)         # Returns: 15
}

# Rounding examples
locals {
  round_to_int = provider::pyvider::round(3.7, 0)         # Returns: 4
  round_to_decimal = provider::pyvider::round(3.14159, 2) # Returns: 3.14
  round_negative = provider::pyvider::round(-2.6, 0)      # Returns: -3
}

# Output results for verification
output "numeric_examples" {
  value = {
    addition = {
      simple = local.simple_add
      float = local.float_add
      mixed = local.mixed_add
    }
    subtraction = {
      simple = local.simple_subtract
      float = local.float_subtract
      negative = local.negative_result
    }
    multiplication = {
      simple = local.simple_multiply
      float = local.float_multiply
      zero = local.zero_multiply
    }
    division = {
      simple = local.simple_divide
      float = local.float_divide
      precise = local.precise_divide
    }
    list_operations = {
      sum = local.list_sum
      min = local.list_min
      max = local.list_max
    }
    rounding = {
      to_int = local.round_to_int
      to_decimal = local.round_to_decimal
      negative = local.round_negative
    }
  }
}