---
page_title: "Resource: pyvider_local_directory"
description: |-
  Manages directories on the local filesystem with permissions and metadata tracking
---

# pyvider_local_directory (Resource)

> Creates and manages directories with optional permission control and file counting

The `pyvider_local_directory` resource allows you to create, manage, and monitor directories on the local filesystem. It automatically tracks directory metadata including file counts and provides fine-grained permission control.

## When to Use This

- **Project structure**: Create consistent directory layouts for applications
- **Permission management**: Ensure directories have correct access permissions
- **Workspace initialization**: Set up development or deployment environments
- **Directory monitoring**: Track changes in directory contents

**Anti-patterns (when NOT to use):**
- Temporary directories that don't need state tracking
- Directories where you only need to check existence (use `pyvider_file_info` instead)
- Complex recursive operations (handle those with external tools)

## Quick Start

```terraform
# Create a simple directory
resource "pyvider_local_directory" "app_logs" {
  path = "/tmp/app/logs"
}

# Create a directory with specific permissions
resource "pyvider_local_directory" "secure_config" {
  path        = "/tmp/app/config"
  permissions = "0o750"  # rwxr-x---
}

# Access computed attributes
output "log_dir_info" {
  value = {
    id         = pyvider_local_directory.app_logs.id
    file_count = pyvider_local_directory.app_logs.file_count
  }
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Project Structure Creation

{{ example("project_structure") }}

### Permission Management

{{ example("permissions") }}

### Workspace Setup

{{ example("workspace") }}

## Schema

{{ schema() }}

## Import

Directories can be imported into Terraform state using either the CLI or configuration-based import.

### CLI Import

```bash
terraform import pyvider_local_directory.example /path/to/existing/directory
```

### Configuration Import (Terraform 1.5+)

```terraform
import {
  to = pyvider_local_directory.example
  id = "/path/to/existing/directory"
}

resource "pyvider_local_directory" "example" {
  path = "/path/to/existing/directory"
  # permissions will be read during import
}
```

### Import Process

During import, the provider will:
1. Verify the directory exists and is accessible
2. Read the current directory permissions
3. Count the number of files in the directory
4. Store the directory state in Terraform state

**Note**: If you specify `permissions` in your configuration, ensure they match the existing directory permissions, or Terraform will attempt to update them on the next apply.

## Permission Format

The `permissions` attribute uses octal notation with the `0o` prefix:

| Permission | Octal | Description |
|------------|-------|-------------|
| `0o755`    | 755   | rwxr-xr-x (owner: read/write/execute, group/others: read/execute) |
| `0o750`    | 750   | rwxr-x--- (owner: read/write/execute, group: read/execute, others: none) |
| `0o700`    | 700   | rwx------ (owner: read/write/execute, others: none) |
| `0o644`    | 644   | rw-r--r-- (owner: read/write, group/others: read only) |

## Common Issues & Solutions

### Error: "Permission denied"
**Solution**: Ensure the Terraform process has permission to create directories in the target location.

```bash
# Check parent directory permissions
ls -la /path/to/parent
# Fix parent permissions if needed
chmod 755 /path/to/parent
```

### Error: "Invalid permissions format"
**Solution**: Ensure permissions use the correct octal format with `0o` prefix.

```terraform
# ❌ Wrong
resource "pyvider_local_directory" "wrong" {
  path        = "/tmp/test"
  permissions = "755"  # Missing 0o prefix
}

# ✅ Correct
resource "pyvider_local_directory" "correct" {
  path        = "/tmp/test"
  permissions = "0o755"  # Proper octal format
}
```

### Parent Directory Doesn't Exist
**Solution**: Create parent directories first or use depends_on for proper ordering.

```terraform
# Create parent directory first
resource "pyvider_local_directory" "parent" {
  path = "/tmp/app"
}

resource "pyvider_local_directory" "child" {
  path = "/tmp/app/subdirectory"

  depends_on = [pyvider_local_directory.parent]
}
```

### Directory Already Exists with Different Permissions
When importing or managing existing directories, the resource will update permissions to match the configuration.

## File Count Monitoring

The `file_count` attribute provides the number of direct children (files and subdirectories) in the managed directory:

```terraform
resource "pyvider_local_directory" "monitored" {
  path = "/tmp/monitored"
}

# Use file count in conditional logic
resource "pyvider_file_content" "status" {
  filename = "/tmp/status.txt"
  content  = "Directory has ${pyvider_local_directory.monitored.file_count} items"
}
```

## Related Components

- [`pyvider_file_content`](../file_content.md) - Create files within managed directories
- [`pyvider_file_info`](../../data-sources/file_info.md) - Check directory existence without management
- [`env_variables` data source](../../data-sources/env_variables.md) - Use environment variables in directory paths