---
page_title: "Function: contains"
description: |-
  Checks if a list contains a specific element with null-safe handling
---

# contains (Function)

> Tests whether a list contains a specific element with null-safe handling and type-aware comparison

The `contains` function searches through a list to determine if it contains a specific element. It performs exact matching and handles null values gracefully, returning a boolean result.

## When to Use This

- **Validation**: Check if required values are present in lists
- **Conditional logic**: Make decisions based on list membership
- **Security checks**: Verify if values are in allowlists or blocklists
- **Feature toggles**: Check if features are enabled in configuration lists
- **Data filtering**: Determine if items meet criteria

**Anti-patterns (when NOT to use):**
- Map/object key checking (use map lookup instead)
- String substring search (use string functions)
- Complex object matching (use custom logic)
- Performance-critical paths with very large lists

## Quick Start

```terraform
# Simple containment check
locals {
  allowed_envs = ["dev", "staging", "production"]
  current_env = "production"
  is_valid_env = provider::pyvider::contains(local.allowed_envs, local.current_env)  # Returns: true
}

# Security validation
locals {
  blocked_ips = ["192.168.1.100", "10.0.0.50"]
  client_ip = "192.168.1.100"
  is_blocked = provider::pyvider::contains(local.blocked_ips, local.client_ip)  # Returns: true
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Security and Validation

{{ example("security_validation") }}

### Configuration Checks

{{ example("configuration_checks") }}

### Feature Toggles

{{ example("feature_toggles") }}

## Signature

`contains(list_to_check: list[any], element: any) -> boolean`

## Arguments

- **`list_to_check`** (list[any], required) - The list to search within. Returns `null` if this value is `null`.
- **`element`** (any, required) - The element to search for. Can be any type (string, number, boolean, etc.).

## Return Value

Returns a boolean indicating whether the element was found:
- `true` if the element exists in the list
- `false` if the element does not exist in the list
- Returns `null` if the input list is `null`
- Uses exact equality comparison (type and value must match)

## Behavior Details

### Type-Sensitive Matching
```terraform
locals {
  mixed_list = [1, "1", true, "true"]

  checks = {
    number_1 = provider::pyvider::contains(local.mixed_list, 1)      # true
    string_1 = provider::pyvider::contains(local.mixed_list, "1")    # true
    bool_true = provider::pyvider::contains(local.mixed_list, true)   # true
    string_true = provider::pyvider::contains(local.mixed_list, "true") # true

    # These are different types, so they don't match
    number_vs_string = provider::pyvider::contains(local.mixed_list, "2") # false ("2" not in list)
  }
}
```

### Null Handling
```terraform
locals {
  list_with_null = ["a", null, "b"]

  checks = {
    has_null = provider::pyvider::contains(local.list_with_null, null)    # true
    null_list = provider::pyvider::contains(null, "value")                # null
  }
}
```

### Empty List Handling
```terraform
locals {
  empty_list = []
  result = provider::pyvider::contains(local.empty_list, "anything")  # false
}
```

## Common Patterns

### Environment Validation
```terraform
variable "environment" {
  type = string
}

locals {
  valid_environments = ["development", "staging", "production"]
  is_valid_env = provider::pyvider::contains(local.valid_environments, var.environment)
}

resource "pyvider_file_content" "env_check" {
  count = local.is_valid_env ? 1 : 0

  filename = "/tmp/environment.txt"
  content  = "Environment ${var.environment} is valid"
}
```

### Feature Toggle Management
```terraform
variable "enabled_features" {
  type = list(string)
  default = ["feature_a", "feature_c"]
}

locals {
  feature_flags = {
    analytics_enabled = provider::pyvider::contains(var.enabled_features, "analytics")
    debug_enabled = provider::pyvider::contains(var.enabled_features, "debug")
    feature_a_enabled = provider::pyvider::contains(var.enabled_features, "feature_a")
  }
}

resource "pyvider_file_content" "feature_config" {
  filename = "/tmp/features.conf"
  content = join("\n", [
    "analytics=${local.feature_flags.analytics_enabled}",
    "debug=${local.feature_flags.debug_enabled}",
    "feature_a=${local.feature_flags.feature_a_enabled}"
  ])
}
```

### Security Allowlist/Blocklist
```terraform
variable "client_ip" {
  type = string
}

variable "allowed_ips" {
  type = list(string)
  default = ["192.168.1.0/24", "10.0.0.100", "203.0.113.50"]
}

variable "blocked_ips" {
  type = list(string)
  default = ["192.168.1.100", "10.0.0.50"]
}

locals {
  is_allowed = provider::pyvider::contains(var.allowed_ips, var.client_ip)
  is_blocked = provider::pyvider::contains(var.blocked_ips, var.client_ip)
  access_granted = local.is_allowed && !local.is_blocked
}

resource "pyvider_file_content" "access_decision" {
  filename = "/tmp/access.log"
  content = join("\n", [
    "Client IP: ${var.client_ip}",
    "Allowed: ${local.is_allowed}",
    "Blocked: ${local.is_blocked}",
    "Access Granted: ${local.access_granted}"
  ])
}
```

### Configuration Validation
```terraform
variable "deployment_strategy" {
  type = string
}

variable "service_tier" {
  type = string
}

locals {
  valid_strategies = ["blue-green", "rolling", "canary"]
  valid_tiers = ["free", "basic", "premium", "enterprise"]

  config_valid = (
    provider::pyvider::contains(local.valid_strategies, var.deployment_strategy) &&
    provider::pyvider::contains(local.valid_tiers, var.service_tier)
  )
}

resource "pyvider_file_content" "deployment_config" {
  count = local.config_valid ? 1 : 0

  filename = "/tmp/deployment.yaml"
  content = join("\n", [
    "strategy: ${var.deployment_strategy}",
    "tier: ${var.service_tier}",
    "validated: true"
  ])
}
```

## Best Practices

### 1. Validate Input Types
```terraform
variable "search_list" {
  type = list(string)
  validation {
    condition     = length(var.search_list) >= 0
    error_message = "Search list must be valid."
  }
}

variable "search_value" {
  type = string
}

locals {
  found = provider::pyvider::contains(var.search_list, var.search_value)
}
```

### 2. Handle Null Cases
```terraform
locals {
  safe_contains = var.optional_list != null ? provider::pyvider::contains(var.optional_list, var.value) : false
}
```

### 3. Use with Conditional Logic
```terraform
locals {
  requires_special_handling = provider::pyvider::contains(var.special_cases, var.current_case)

  processing_mode = local.requires_special_handling ? "special" : "standard"
}
```

### 4. Combine with Other Functions
```terraform
# Check multiple conditions
locals {
  critical_environments = ["production", "staging"]
  is_critical = provider::pyvider::contains(local.critical_environments, var.environment)

  # Use with length for validation
  has_required_tags = provider::pyvider::length(var.tags) > 0
  has_env_tag = provider::pyvider::contains(var.tags, "environment:${var.environment}")

  deployment_ready = local.is_critical ? (local.has_required_tags && local.has_env_tag) : local.has_required_tags
}
```

## Related Functions

- [`length`](./length.md) - Get the size of collections
- [`lookup`](./lookup.md) - Look up values in maps (for key-value searches)
- [`split`](../string_manipulation/split.md) - Split strings to create searchable lists
- [`join`](../string_manipulation/join.md) - Join lists after filtering
