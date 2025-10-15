---
page_title: "Resource: pyvider_file_content"
description: |-
  Manages the content of a file on the local filesystem
---

# pyvider_file_content (Resource)

> Manages file content with atomic writes and content tracking

The `pyvider_file_content` resource allows you to create, read, update, and delete files on the local filesystem. It automatically tracks content changes using SHA256 hashing and provides atomic write operations to ensure file integrity.

## When to Use This

- **Configuration files**: Create and manage application config files
- **Template rendering**: Generate files from dynamic content
- **Atomic file operations**: Ensure file writes are safe and complete
- **Content tracking**: Monitor file changes with automatic hash calculation

**Anti-patterns (when NOT to use):**
- Large binary files (use file operations instead)
- Temporary files that don't need state tracking
- Files requiring special permissions (use `local_directory` for permission management)

## Quick Start

```terraform
# Create a simple configuration file
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/app.conf"
  content  = "DATABASE_URL=localhost:5432"
}

# Access the computed attributes
output "config_exists" {
  value = pyvider_file_content.app_config.exists
}

output "config_hash" {
  value = pyvider_file_content.app_config.content_hash
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Template-Based Configuration

{{ example("template") }}

### Multi-Line Content

{{ example("multiline") }}

### Environment-Specific Files

{{ example("environment") }}

## Schema

{{ schema() }}

## Import

Files can be imported into Terraform state using either the CLI or configuration-based import.

### CLI Import

```bash
terraform import pyvider_file_content.example /path/to/existing/file.txt
```

### Configuration Import (Terraform 1.5+)

```terraform
import {
  to = pyvider_file_content.example
  id = "/path/to/existing/file.txt"
}

resource "pyvider_file_content" "example" {
  filename = "/path/to/existing/file.txt"
  content  = "existing content will be read during import"
}
```

### Import Process

During import, the provider will:
1. Read the current file content from the specified path
2. Calculate the SHA256 hash of the content
3. Set the `exists` attribute to `true`
4. Store the content and hash in Terraform state

**Note**: The `content` attribute in your configuration should match the existing file content, or Terraform will detect a drift and attempt to update the file on the next apply.

## Common Issues & Solutions

### Error: "Permission denied"
**Solution**: Ensure the Terraform process has write permissions to the target directory and file.

```bash
# Check permissions
ls -la /path/to/directory
# Fix permissions if needed
chmod 755 /path/to/directory
chmod 644 /path/to/file
```

### Error: "No such file or directory"
**Solution**: Ensure the parent directory exists before creating the file.

```terraform
# Create parent directory first
resource "pyvider_local_directory" "config_dir" {
  path = "/etc/myapp"
}

resource "pyvider_file_content" "config" {
  filename = "${pyvider_local_directory.config_dir.path}/app.conf"
  content  = "key=value"

  depends_on = [pyvider_local_directory.config_dir]
}
```

### Handling Large Files
For files larger than a few MB, consider alternative approaches:

```terraform
# For large static files, use data source instead
data "pyvider_file_info" "large_file" {
  filename = "/path/to/large/file"
}
```

## Related Components

- [`pyvider_local_directory`](../local_directory.md) - Manage directories and permissions
- [`pyvider_file_info`](../../data-sources/file_info.md) - Read file metadata without managing content
- [`format` function](../../functions/string/format.md) - Generate dynamic content for files
- [`env_variables` data source](../../data-sources/env_variables.md) - Include environment variables in file content