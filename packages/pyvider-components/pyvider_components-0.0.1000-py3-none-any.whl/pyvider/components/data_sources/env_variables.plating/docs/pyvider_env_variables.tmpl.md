---
page_title: "Data Source: pyvider_env_variables"
description: |-
  Provides access to environment variables with filtering and transformation capabilities
---

# pyvider_env_variables (Data Source)

> Read and filter environment variables with powerful transformation options

The `pyvider_env_variables` data source allows you to access environment variables from the system where Terraform is running. It provides flexible filtering by keys, prefixes, or regex patterns, plus built-in transformations for keys and values.

## When to Use This

- **Configuration management**: Read environment-specific settings
- **Multi-environment deployments**: Access different configs per environment
- **Secrets injection**: Pull sensitive values from environment variables
- **Dynamic configuration**: Use environment state to influence resource creation
- **CI/CD integration**: Access build/deployment variables

**Anti-patterns (when NOT to use):**
- Hardcoded secrets (use proper secret management instead)
- Large amounts of configuration data (use config files)
- Complex data structures (environment variables are strings only)

## Quick Start

```terraform
# Read specific environment variables
data "pyvider_env_variables" "app_config" {
  keys = ["DATABASE_URL", "API_KEY", "DEBUG"]
}

# Access the values
resource "pyvider_file_content" "config" {
  filename = "/tmp/app.conf"
  content = "DATABASE_URL=${lookup(data.pyvider_env_variables.app_config.values, "DATABASE_URL", "localhost")}"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Filtering and Transformations

{{ example("filtering") }}

### Sensitive Variable Handling

{{ example("sensitive") }}

### Multi-Environment Configuration

{{ example("multi_environment") }}

## Schema

{{ schema() }}

## Filtering Options

The data source provides multiple ways to filter environment variables:

### By Specific Keys
```terraform
data "pyvider_env_variables" "specific" {
  keys = ["PATH", "HOME", "USER"]
}
```

### By Prefix
```terraform
data "pyvider_env_variables" "app_vars" {
  prefix = "MYAPP_"  # Matches MYAPP_DATABASE_URL, MYAPP_DEBUG, etc.
}
```

### By Regex Pattern
```terraform
data "pyvider_env_variables" "pattern_match" {
  regex = ".*_URL$"  # Matches any variable ending in _URL
}
```

## Transformations

### Key Transformations
Transform variable names before returning:

- `"lower"` - Convert to lowercase
- `"upper"` - Convert to uppercase

### Value Transformations
Transform variable values:

- `"lower"` - Convert values to lowercase
- `"upper"` - Convert values to uppercase

### Case Sensitivity
Control case-sensitive matching:

```terraform
data "pyvider_env_variables" "case_insensitive" {
  prefix         = "myapp_"
  case_sensitive = false  # Matches MYAPP_, MyApp_, myapp_, etc.
}
```

## Sensitive Variables

Use the `sensitive_keys` parameter to mark certain variables as sensitive:

```terraform
data "pyvider_env_variables" "with_secrets" {
  keys           = ["API_KEY", "DATABASE_PASSWORD", "PUBLIC_CONFIG"]
  sensitive_keys = ["API_KEY", "DATABASE_PASSWORD"]
}

# sensitive_values contains only the sensitive ones
# values contains only the non-sensitive ones
# all_values contains everything (marked as sensitive)
```

## Empty Variable Handling

By default, empty environment variables are excluded. Control this with `exclude_empty`:

```terraform
data "pyvider_env_variables" "include_empty" {
  prefix        = "OPTIONAL_"
  exclude_empty = false  # Include variables that exist but are empty
}
```

## Output Attributes

The data source provides several output attributes:

- **`values`** - Non-sensitive variables as a map
- **`sensitive_values`** - Sensitive variables as a map (marked sensitive)
- **`all_values`** - All variables combined (marked sensitive if any are sensitive)
- **`all_environment`** - Complete environment snapshot

## Common Patterns

### Environment-Specific Configuration
```terraform
data "pyvider_env_variables" "env_config" {
  prefix = "${upper(var.environment)}_"
}

locals {
  database_url = lookup(
    data.pyvider_env_variables.env_config.values,
    "${upper(var.environment)}_DATABASE_URL",
    "postgresql://localhost:5432/default"
  )
}
```

### Feature Flag Management
```terraform
data "pyvider_env_variables" "feature_flags" {
  prefix = "FEATURE_"
  transform_keys = "lower"  # FEATURE_NEW_UI becomes feature_new_ui
}

locals {
  features = {
    for key, value in data.pyvider_env_variables.feature_flags.values :
    replace(key, "feature_", "") => value == "true"
  }
}
```

## Common Issues & Solutions

### Error: "Environment variable not found"
**Solution**: Use `lookup()` with default values for optional variables.

```terraform
# ❌ Will fail if OPTIONAL_VAR doesn't exist
locals {
  config = data.pyvider_env_variables.config.values["OPTIONAL_VAR"]
}

# ✅ Provides fallback value
locals {
  config = lookup(data.pyvider_env_variables.config.values, "OPTIONAL_VAR", "default")
}
```

### Handling Multiline Values
Environment variables containing newlines need special handling:

```terraform
data "pyvider_env_variables" "multiline" {
  keys = ["CERTIFICATE_PEM"]
}

resource "pyvider_file_content" "cert" {
  filename = "/tmp/cert.pem"
  content  = data.pyvider_env_variables.multiline.values["CERTIFICATE_PEM"]
}
```

### Boolean Environment Variables
Convert string environment variables to booleans:

```terraform
data "pyvider_env_variables" "flags" {
  prefix = "ENABLE_"
}

locals {
  boolean_flags = {
    for key, value in data.pyvider_env_variables.flags.values :
    key => contains(["true", "1", "yes", "on"], lower(value))
  }
}
```

## Security Best Practices

1. **Use `sensitive_keys`** for any secrets or credentials
2. **Avoid logging** sensitive environment variables
3. **Use least privilege** - only read variables you need
4. **Validate inputs** - environment variables are user-controlled
5. **Use defaults** - handle missing variables gracefully

## Related Components

- [`pyvider_file_content`](../../resources/file_content.md) - Write environment-based configuration files
- [`pyvider_provider_config_reader`](../provider_config_reader.md) - Access provider configuration
- [String functions](../../functions/string/) - Transform environment variable values