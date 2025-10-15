# Basic directory creation and management

# Create a simple directory
resource "pyvider_local_directory" "basic_dir" {
  path = "/tmp/pyvider_basic"
}

# Create a directory with specific permissions
resource "pyvider_local_directory" "secure_dir" {
  path        = "/tmp/pyvider_secure"
  permissions = "0o700"  # Only owner can read/write/execute
}

# Create multiple related directories
resource "pyvider_local_directory" "app_root" {
  path = "/tmp/myapp"
}

resource "pyvider_local_directory" "app_logs" {
  path        = "/tmp/myapp/logs"
  permissions = "0o755"

  depends_on = [pyvider_local_directory.app_root]
}

resource "pyvider_local_directory" "app_data" {
  path        = "/tmp/myapp/data"
  permissions = "0o750"  # More restrictive for data directory

  depends_on = [pyvider_local_directory.app_root]
}

# Add some files to demonstrate file counting
resource "pyvider_file_content" "log_file" {
  filename = "${pyvider_local_directory.app_logs.path}/app.log"
  content  = "Application started at ${timestamp()}"

  depends_on = [pyvider_local_directory.app_logs]
}

resource "pyvider_file_content" "config_file" {
  filename = "${pyvider_local_directory.app_root.path}/config.ini"
  content = join("\n", [
    "[database]",
    "host=localhost",
    "port=5432",
    "",
    "[logging]",
    "level=INFO",
    "file=${pyvider_local_directory.app_logs.path}/app.log"
  ])

  depends_on = [pyvider_local_directory.app_root]
}

output "directory_info" {
  description = "Information about created directories"
  value = {
    basic = {
      path       = pyvider_local_directory.basic_dir.path
      id         = pyvider_local_directory.basic_dir.id
      file_count = pyvider_local_directory.basic_dir.file_count
    }
    secure = {
      path        = pyvider_local_directory.secure_dir.path
      permissions = pyvider_local_directory.secure_dir.permissions
      file_count  = pyvider_local_directory.secure_dir.file_count
    }
    app_structure = {
      root = {
        path       = pyvider_local_directory.app_root.path
        file_count = pyvider_local_directory.app_root.file_count  # Should show 1 (config.ini)
      }
      logs = {
        path       = pyvider_local_directory.app_logs.path
        file_count = pyvider_local_directory.app_logs.file_count  # Should show 1 (app.log)
        permissions = pyvider_local_directory.app_logs.permissions
      }
      data = {
        path        = pyvider_local_directory.app_data.path
        file_count  = pyvider_local_directory.app_data.file_count  # Should show 0
        permissions = pyvider_local_directory.app_data.permissions
      }
    }
  }
}