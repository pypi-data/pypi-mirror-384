---
page_title: "Function: max"
description: |-
  Finds the maximum value in a list of numbers with error handling for empty lists
---

# max (Function)

> Finds the largest numeric value in a list with null-safe handling and empty list validation

The `max` function finds and returns the largest number from a list of numbers. It requires at least one number in the list and handles null values gracefully.

## When to Use This

- **Capacity planning**: Find maximum resource requirements
- **Performance optimization**: Identify peak performance values
- **Scaling decisions**: Determine maximum load or usage
- **Budget planning**: Find highest costs or allocations
- **Quality metrics**: Identify best performance indicators

**Anti-patterns (when NOT to use):**
- Empty lists (will cause an error)
- Single-value comparisons (just use the value directly)
- Non-numeric data (ensure list contains only numbers)

## Quick Start

```terraform
# Simple maximum
locals {
  scores = [85, 92, 78, 96, 88]
  highest_score = provider::pyvider::max(local.scores)  # Returns: 96
}

# Resource maximum
variable "memory_usage_gb" {
  default = [2.5, 8.1, 4.3, 12.7]
}

locals {
  peak_memory = provider::pyvider::max(var.memory_usage_gb)  # Returns: 12.7
}
```

## Examples

### Basic Usage

```terraform
# Simple maximum value finding
locals {
  basic_examples = {
    scores = [85, 92, 78, 96, 88]
    highest_score = provider::pyvider::max(local.basic_examples.scores)  # 96

    prices = [19.99, 35.50, 22.00, 48.75, 18.25]
    highest_price = provider::pyvider::max(local.basic_examples.prices)  # 48.75

    temperatures = [-5, 12, 8, 25, 15, 3]
    highest_temp = provider::pyvider::max(local.basic_examples.temperatures)  # 25

    response_times = [250.5, 180.2, 520.8, 195.1, 275.6]
    slowest_response = provider::pyvider::max(local.basic_examples.response_times)  # 520.8
  }

  # Working with variables
  memory_usage_samples = [2.5, 4.2, 8.8, 3.1, 6.5, 7.2, 5.8]
  peak_memory_usage = provider::pyvider::max(local.memory_usage_samples)  # 8.8

  # Mixed integer and float values
  mixed_values = [10, 17.5, 12, 9.2, 8, 15.8]
  maximum_mixed = provider::pyvider::max(local.mixed_values)  # 17.5

  # Single value list
  single_value = [42]
  single_max = provider::pyvider::max(local.single_value)  # 42
}

# Error prevention with validation
variable "user_scores" {
  type = list(number)
  default = []
}

locals {
  # Safe maximum calculation with empty list check
  has_scores = length(var.user_scores) > 0
  max_score = local.has_scores ? provider::pyvider::max(var.user_scores) : null

  # Conditional maximum with fallback
  default_values = [1, 2, 3]
  safe_maximum = length(var.user_scores) > 0 ?
    provider::pyvider::max(var.user_scores) :
    provider::pyvider::max(local.default_values)
}

output "basic_max_examples" {
  value = {
    examples = local.basic_examples
    peak_memory = local.peak_memory_usage
    mixed_maximum = local.maximum_mixed
    safe_handling = {
      has_data = local.has_scores
      maximum = local.max_score
      fallback_maximum = local.safe_maximum
    }
  }
}
```

### Infrastructure Capacity Planning

```terraform
# Server capacity analysis across multiple environments
variable "server_resources" {
  type = map(object({
    cpu_cores = list(number)
    memory_gb = list(number)
    storage_gb = list(number)
    network_mbps = list(number)
  }))
  default = {
    production = {
      cpu_cores = [8, 16, 32, 16, 24]
      memory_gb = [16, 32, 64, 32, 48]
      storage_gb = [500, 1000, 2000, 1000, 1500]
      network_mbps = [1000, 1000, 10000, 1000, 1000]
    }
    staging = {
      cpu_cores = [4, 8, 8, 4]
      memory_gb = [8, 16, 16, 8]
      storage_gb = [200, 500, 500, 200]
      network_mbps = [100, 1000, 1000, 100]
    }
    development = {
      cpu_cores = [2, 4, 2]
      memory_gb = [4, 8, 4]
      storage_gb = [100, 200, 100]
      network_mbps = [100, 100, 100]
    }
  }
}

# Find maximum resource requirements per environment
locals {
  capacity_analysis = {
    for env_name, resources in var.server_resources :
    env_name => {
      # Find maximum resource usage
      max_cpu = provider::pyvider::max(resources.cpu_cores)
      max_memory = provider::pyvider::max(resources.memory_gb)
      max_storage = provider::pyvider::max(resources.storage_gb)
      max_network = provider::pyvider::max(resources.network_mbps)

      # Calculate total resource capacity
      total_cpu = sum(resources.cpu_cores)
      total_memory = sum(resources.memory_gb)
      total_storage = sum(resources.storage_gb)

      # Calculate resource concentration (how much is on the biggest server)
      cpu_concentration = round((local.capacity_analysis[env_name].max_cpu / local.capacity_analysis[env_name].total_cpu) * 100, 1)
      memory_concentration = round((local.capacity_analysis[env_name].max_memory / local.capacity_analysis[env_name].total_memory) * 100, 1)
      storage_concentration = round((local.capacity_analysis[env_name].max_storage / local.capacity_analysis[env_name].total_storage) * 100, 1)

      # Identify potential scaling needs (when max usage is high)
      needs_cpu_scaling = local.capacity_analysis[env_name].max_cpu >= 24
      needs_memory_scaling = local.capacity_analysis[env_name].max_memory >= 48
      needs_storage_scaling = local.capacity_analysis[env_name].max_storage >= 1500

      # Risk assessment based on resource concentration
      high_concentration_risk = (
        local.capacity_analysis[env_name].cpu_concentration > 40 ||
        local.capacity_analysis[env_name].memory_concentration > 40 ||
        local.capacity_analysis[env_name].storage_concentration > 40
      )

      # Recommended scaling actions
      scaling_recommendations = compact([
        local.capacity_analysis[env_name].needs_cpu_scaling ? "Scale CPU: Add more CPU-optimized instances" : "",
        local.capacity_analysis[env_name].needs_memory_scaling ? "Scale Memory: Add memory-optimized instances" : "",
        local.capacity_analysis[env_name].needs_storage_scaling ? "Scale Storage: Add high-capacity storage" : "",
        local.capacity_analysis[env_name].high_concentration_risk ? "Distribute Load: Reduce single-point-of-failure risk" : ""
      ])
    }
  }

  # Cross-environment capacity comparison
  global_capacity = {
    # Find highest resource usage across all environments
    all_cpu_values = flatten([for env, resources in var.server_resources : resources.cpu_cores])
    all_memory_values = flatten([for env, resources in var.server_resources : resources.memory_gb])
    all_storage_values = flatten([for env, resources in var.server_resources : resources.storage_gb])

    global_max_cpu = provider::pyvider::max(local.global_capacity.all_cpu_values)
    global_max_memory = provider::pyvider::max(local.global_capacity.all_memory_values)
    global_max_storage = provider::pyvider::max(local.global_capacity.all_storage_values)

    # Identify which environment has peak resources
    peak_cpu_env = [
      for env_name, analysis in local.capacity_analysis : env_name
      if analysis.max_cpu == local.global_capacity.global_max_cpu
    ][0]

    peak_memory_env = [
      for env_name, analysis in local.capacity_analysis : env_name
      if analysis.max_memory == local.global_capacity.global_max_memory
    ][0]

    peak_storage_env = [
      for env_name, analysis in local.capacity_analysis : env_name
      if analysis.max_storage == local.global_capacity.global_max_storage
    ][0]
  }
}

output "capacity_planning" {
  value = {
    environment_analysis = local.capacity_analysis
    global_analysis = local.global_capacity
  }
}
```

### Performance Optimization

```terraform
# Application performance metrics analysis
variable "performance_metrics" {
  type = map(object({
    response_times_ms = list(number)
    requests_per_second = list(number)
    error_rates_percent = list(number)
    cpu_usage_percent = list(number)
    memory_usage_percent = list(number)
  }))
  default = {
    api_gateway = {
      response_times_ms = [120, 95, 340, 88, 105, 430, 92, 515]
      requests_per_second = [850, 920, 780, 1250, 890, 960, 820, 1150]
      error_rates_percent = [0.2, 0.1, 2.3, 0.15, 0.08, 1.85, 0.12, 0.98]
      cpu_usage_percent = [45, 52, 78, 61, 48, 82, 42, 75]
      memory_usage_percent = [65, 72, 88, 78, 62, 91, 60, 85]
    }
    database = {
      response_times_ms = [25, 18, 152, 22, 28, 98, 35, 67]
      requests_per_second = [1200, 1350, 1100, 1480, 1320, 1180, 1250, 1380]
      error_rates_percent = [0.05, 0.02, 0.28, 0.03, 0.06, 0.15, 0.07, 0.12]
      cpu_usage_percent = [30, 28, 65, 32, 29, 58, 31, 45]
      memory_usage_percent = [82, 85, 92, 87, 80, 94, 81, 89]
    }
    cache_service = {
      response_times_ms = [5, 3, 27, 4, 6, 18, 8, 15]
      requests_per_second = [2800, 3100, 2600, 3350, 3050, 2750, 2900, 3200]
      error_rates_percent = [0.01, 0.0, 0.12, 0.01, 0.0, 0.08, 0.02, 0.05]
      cpu_usage_percent = [15, 18, 42, 22, 16, 35, 14, 28]
      memory_usage_percent = [45, 48, 67, 52, 44, 73, 43, 58]
    }
  }
}

# Analyze peak performance and identify bottlenecks
locals {
  performance_analysis = {
    for service_name, metrics in var.performance_metrics :
    service_name => {
      # Find peak (worst) performance values
      max_response_time = provider::pyvider::max(metrics.response_times_ms)
      max_error_rate = provider::pyvider::max(metrics.error_rates_percent)
      max_cpu_usage = provider::pyvider::max(metrics.cpu_usage_percent)
      max_memory_usage = provider::pyvider::max(metrics.memory_usage_percent)

      # Find peak (best) throughput
      max_requests_per_second = provider::pyvider::max(metrics.requests_per_second)

      # Performance thresholds (SLA targets)
      sla_thresholds = {
        max_allowed_response_time = service_name == "api_gateway" ? 200 : service_name == "database" ? 50 : 10
        max_allowed_error_rate = 1.0
        max_allowed_cpu = 80
        max_allowed_memory = 90
      }

      # SLA compliance analysis
      response_time_violations = local.performance_analysis[service_name].max_response_time > local.performance_analysis[service_name].sla_thresholds.max_allowed_response_time
      error_rate_violations = local.performance_analysis[service_name].max_error_rate > local.performance_analysis[service_name].sla_thresholds.max_allowed_error_rate
      cpu_violations = local.performance_analysis[service_name].max_cpu_usage > local.performance_analysis[service_name].sla_thresholds.max_allowed_cpu
      memory_violations = local.performance_analysis[service_name].max_memory_usage > local.performance_analysis[service_name].sla_thresholds.max_allowed_memory

      # Calculate performance headroom (distance to limits)
      response_time_headroom = local.performance_analysis[service_name].sla_thresholds.max_allowed_response_time - local.performance_analysis[service_name].max_response_time
      cpu_headroom = local.performance_analysis[service_name].sla_thresholds.max_allowed_cpu - local.performance_analysis[service_name].max_cpu_usage
      memory_headroom = local.performance_analysis[service_name].sla_thresholds.max_allowed_memory - local.performance_analysis[service_name].max_memory_usage

      # Service health status
      health_status = (
        local.performance_analysis[service_name].response_time_violations ||
        local.performance_analysis[service_name].error_rate_violations ||
        local.performance_analysis[service_name].cpu_violations ||
        local.performance_analysis[service_name].memory_violations
      ) ? "critical" : (
        local.performance_analysis[service_name].response_time_headroom < 20 ||
        local.performance_analysis[service_name].cpu_headroom < 10 ||
        local.performance_analysis[service_name].memory_headroom < 5
      ) ? "warning" : "healthy"

      # Optimization recommendations based on peak values
      optimization_recommendations = compact([
        local.performance_analysis[service_name].response_time_violations ? "Optimize response time: Consider caching or query optimization" : "",
        local.performance_analysis[service_name].error_rate_violations ? "Reduce error rate: Improve error handling and input validation" : "",
        local.performance_analysis[service_name].cpu_violations ? "Scale CPU: Add more CPU cores or optimize CPU-intensive operations" : "",
        local.performance_analysis[service_name].memory_violations ? "Scale memory: Increase memory allocation or optimize memory usage" : ""
      ])
    }
  }

  # System-wide performance summary
  system_performance = {
    # Find service with worst (maximum) performance issues
    all_max_response_times = [for service_name, analysis in local.performance_analysis : analysis.max_response_time]
    worst_response_time_overall = provider::pyvider::max(local.system_performance.all_max_response_times)

    all_max_error_rates = [for service_name, analysis in local.performance_analysis : analysis.max_error_rate]
    worst_error_rate_overall = provider::pyvider::max(local.system_performance.all_max_error_rates)

    all_max_cpu_usage = [for service_name, analysis in local.performance_analysis : analysis.max_cpu_usage]
    highest_cpu_usage_overall = provider::pyvider::max(local.system_performance.all_max_cpu_usage)

    all_max_memory_usage = [for service_name, analysis in local.performance_analysis : analysis.max_memory_usage]
    highest_memory_usage_overall = provider::pyvider::max(local.system_performance.all_max_memory_usage)

    # Find best (maximum) throughput
    all_max_rps = [for service_name, analysis in local.performance_analysis : analysis.max_requests_per_second]
    best_throughput_overall = provider::pyvider::max(local.system_performance.all_max_rps)

    # Performance leaders and bottlenecks
    bottleneck_service = [
      for service_name, analysis in local.performance_analysis : service_name
      if analysis.max_response_time == local.system_performance.worst_response_time_overall
    ][0]

    throughput_leader = [
      for service_name, analysis in local.performance_analysis : service_name
      if analysis.max_requests_per_second == local.system_performance.best_throughput_overall
    ][0]
  }
}

output "performance_optimization" {
  value = {
    service_analysis = local.performance_analysis
    system_summary = local.system_performance
  }
}

## Signature

`max(numbers: list[number]) -> number`

## Arguments

- **`numbers`** (list[number], required) - A list of numbers to find the maximum from. Must contain at least one number. Returns `null` if the list is `null`. **Raises an error** if the list is empty.

## Return Value

Returns the largest number from the list. Preserves the original type (integer or float) of the maximum value.
- Returns `null` if the input list is `null`
- **Raises an error** if the list is empty

## Error Handling

```terraform
# This will cause an error
locals {
  # Error: max() requires at least one number
  # bad_result = provider::pyvider::max([])
}

# Safe usage with validation
variable "values" {
  type = list(number)
}

locals {
  maximum = length(var.values) > 0 ? provider::pyvider::max(var.values) : null
}
```

## Common Patterns

### Resource Scaling
```terraform
variable "instance_cpu_usage" {
  type = list(number)
  default = [65.2, 82.7, 45.3, 91.8]
}

locals {
  peak_cpu_usage = provider::pyvider::max(var.instance_cpu_usage)
  scale_threshold = 80.0
  needs_scaling = local.peak_cpu_usage > local.scale_threshold
}

resource "pyvider_file_content" "scaling_decision" {
  filename = "/tmp/scaling.txt"
  content  = "Peak CPU: ${local.peak_cpu_usage}%, Scaling needed: ${local.needs_scaling}"
}
```

## Related Functions

- [`min`](./min.md) - Find minimum value in a list
- [`sum`](./sum.md) - Calculate sum of all values in a list
