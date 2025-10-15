---
page_title: "Data Source: pyvider_file_info"
description: |-
  Provides detailed information about files and directories
---

# pyvider_file_info (Data Source)

> Read comprehensive metadata about files and directories without managing them

The `pyvider_file_info` data source allows you to inspect files and directories on the local filesystem. It provides detailed metadata including size, timestamps, permissions, and file type information without creating or managing the files.

## When to Use This

- **Conditional resource creation**: Check if files exist before creating resources
- **File system validation**: Verify expected files are present with correct properties
- **Deployment checks**: Validate configuration files before deployment
- **Backup verification**: Check file sizes and modification times
- **Permission auditing**: Inspect file and directory permissions

**Anti-patterns (when NOT to use):**
- Managing file content (use `pyvider_file_content` resource instead)
- Creating or modifying files (this is read-only)
- Complex file operations (use external tools)

## Quick Start

```terraform
# Check if a configuration file exists
data "pyvider_file_info" "config" {
  path = "/etc/myapp/config.yaml"
}

# Conditionally create backup based on file existence
resource "pyvider_file_content" "backup" {
  count = data.pyvider_file_info.config.exists ? 1 : 0

  filename = "/backup/config.yaml.bak"
  content  = "Backup created at ${timestamp()}"
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Conditional Logic

{{ example("conditional") }}

### File System Validation

{{ example("validation") }}

### Permission Checking

{{ example("permissions") }}

## Schema

{{ schema() }}

## Output Attributes

The data source provides comprehensive file information:

### Basic Properties
- **`exists`** - Whether the path exists
- **`size`** - File size in bytes (0 for directories)
- **`is_file`** - True if it's a regular file
- **`is_dir`** - True if it's a directory
- **`is_symlink`** - True if it's a symbolic link

### Timestamps
- **`modified_time`** - Last modification time (ISO 8601 format)
- **`access_time`** - Last access time (ISO 8601 format)
- **`creation_time`** - File creation time (ISO 8601 format)

### Security & Ownership
- **`permissions`** - File permissions in octal format (e.g., "0644")
- **`owner`** - File owner username
- **`group`** - File group name

### Content Information
- **`mime_type`** - MIME type of the file (e.g., "text/plain", "application/json")

## Common Patterns

### Conditional Resource Creation
```terraform
data "pyvider_file_info" "ssl_cert" {
  path = "/etc/ssl/certs/app.crt"
}

# Only create certificate if it doesn't exist
resource "pyvider_file_content" "ssl_cert" {
  count = !data.pyvider_file_info.ssl_cert.exists ? 1 : 0

  filename = "/etc/ssl/certs/app.crt"
  content  = var.ssl_certificate_content
}
```

### File Validation
```terraform
data "pyvider_file_info" "config" {
  path = "/app/config.json"
}

locals {
  config_valid = (
    data.pyvider_file_info.config.exists &&
    data.pyvider_file_info.config.is_file &&
    data.pyvider_file_info.config.size > 0 &&
    data.pyvider_file_info.config.mime_type == "application/json"
  )
}
```

### Permission Auditing
```terraform
data "pyvider_file_info" "sensitive_file" {
  path = "/etc/secrets/api_key"
}

locals {
  secure_permissions = data.pyvider_file_info.sensitive_file.permissions == "0600"
  correct_owner = data.pyvider_file_info.sensitive_file.owner == "app"
}
```

### Backup Decision Logic
```terraform
data "pyvider_file_info" "database_dump" {
  path = "/backups/db_dump.sql"
}

# Create new backup if file is older than 24 hours
locals {
  backup_age_hours = (
    parseint(formatdate("YYYYMMDDhhmm", timestamp()), 10) -
    parseint(formatdate("YYYYMMDDhhmm", data.pyvider_file_info.database_dump.modified_time), 10)
  ) / 100  # Rough calculation

  needs_backup = (
    !data.pyvider_file_info.database_dump.exists ||
    local.backup_age_hours > 24
  )
}
```

## File Size Interpretation

The `size` attribute returns bytes. For human-readable sizes:

```terraform
locals {
  file_size_kb = data.pyvider_file_info.large_file.size / 1024
  file_size_mb = data.pyvider_file_info.large_file.size / (1024 * 1024)
  file_size_gb = data.pyvider_file_info.large_file.size / (1024 * 1024 * 1024)
}
```

## Timestamp Formats

All timestamps are returned in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`):

```terraform
locals {
  # Extract components
  modified_date = split("T", data.pyvider_file_info.example.modified_time)[0]
  modified_time = split("T", data.pyvider_file_info.example.modified_time)[1]

  # Age calculation
  is_recent = timecmp(
    data.pyvider_file_info.example.modified_time,
    timeadd(timestamp(), "-1h")
  ) > 0
}
```

## Permission Format

Permissions are returned in octal format with leading zero:

| Permission | Meaning |
|------------|---------|
| `0644` | rw-r--r-- (owner: read/write, others: read) |
| `0755` | rwxr-xr-x (owner: read/write/execute, others: read/execute) |
| `0600` | rw------- (owner: read/write only) |
| `0700` | rwx------ (owner: read/write/execute only) |

## Common Issues & Solutions

### Error: "Path not found"
This is expected behavior when checking if files exist:

```terraform
# ✅ Correct - handle non-existent files gracefully
data "pyvider_file_info" "optional_file" {
  path = "/optional/config.conf"
}

locals {
  use_defaults = !data.pyvider_file_info.optional_file.exists
}
```

### Symlink Handling
For symbolic links, the data source reports information about the link itself, not the target:

```terraform
data "pyvider_file_info" "symlink" {
  path = "/etc/current-config"  # Points to /etc/configs/v1.2.3/config.yaml
}

# This will be true if it's a symlink, regardless of target validity
output "is_symlink" {
  value = data.pyvider_file_info.symlink.is_symlink
}
```

### Directory vs File Detection
```terraform
data "pyvider_file_info" "path" {
  path = "/var/log"
}

locals {
  path_type = (
    data.pyvider_file_info.path.is_file ? "file" :
    data.pyvider_file_info.path.is_dir ? "directory" :
    data.pyvider_file_info.path.is_symlink ? "symlink" :
    "unknown"
  )
}
```

## Security Considerations

1. **Permission Validation**: Always check file permissions for sensitive files
2. **Owner Verification**: Verify files are owned by expected users
3. **Path Traversal**: Be careful with dynamic paths from user input
4. **Symbolic Links**: Consider if symlinks pose security risks in your use case

## Related Components

- [`pyvider_file_content`](../../resources/file_content.md) - Create and manage file content
- [`pyvider_local_directory`](../../resources/local_directory.md) - Create and manage directories
- [`pyvider_env_variables`](../env_variables.md) - Use environment variables in file paths