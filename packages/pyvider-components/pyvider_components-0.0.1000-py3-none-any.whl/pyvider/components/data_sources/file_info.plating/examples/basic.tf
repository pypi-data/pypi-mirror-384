# Basic file information examples

# Check a regular file
data "pyvider_file_info" "hosts_file" {
  path = "/etc/hosts"
}

# Check a directory
data "pyvider_file_info" "tmp_dir" {
  path = "/tmp"
}

# Check a potentially non-existent file
data "pyvider_file_info" "config_file" {
  path = "/etc/myapp/config.yaml"
}

# Check current working directory
data "pyvider_file_info" "current_dir" {
  path = "."
}

# Create some files to demonstrate with
resource "pyvider_local_directory" "test_dir" {
  path        = "/tmp/file_info_test"
  permissions = "0755"
}

resource "pyvider_file_content" "sample_text" {
  filename = "${pyvider_local_directory.test_dir.path}/sample.txt"
  content  = "This is a sample text file for testing file_info data source."

  depends_on = [pyvider_local_directory.test_dir]
}

resource "pyvider_file_content" "sample_json" {
  filename = "${pyvider_local_directory.test_dir.path}/config.json"
  content = jsonencode({
    app_name = "file_info_demo"
    version  = "1.0.0"
    settings = {
      debug = true
      port  = 8080
    }
  })

  depends_on = [pyvider_local_directory.test_dir]
}

# Check the files we just created
data "pyvider_file_info" "created_text" {
  path = pyvider_file_content.sample_text.filename

  depends_on = [pyvider_file_content.sample_text]
}

data "pyvider_file_info" "created_json" {
  path = pyvider_file_content.sample_json.filename

  depends_on = [pyvider_file_content.sample_json]
}

data "pyvider_file_info" "created_dir" {
  path = pyvider_local_directory.test_dir.path

  depends_on = [pyvider_local_directory.test_dir]
}

# Create a report of all file information
resource "pyvider_file_content" "file_info_report" {
  filename = "/tmp/file_info_basic_report.txt"
  content = join("\n", [
    "=== File Information Report ===",
    "",
    "=== System Files ===",
    "/etc/hosts:",
    "  Exists: ${data.pyvider_file_info.hosts_file.exists}",
    "  Type: ${data.pyvider_file_info.hosts_file.is_file ? "File" : data.pyvider_file_info.hosts_file.is_dir ? "Directory" : "Other"}",
    "  Size: ${data.pyvider_file_info.hosts_file.size} bytes",
    "  Modified: ${data.pyvider_file_info.hosts_file.modified_time}",
    "  Permissions: ${data.pyvider_file_info.hosts_file.permissions}",
    "  Owner: ${data.pyvider_file_info.hosts_file.owner}",
    "  MIME Type: ${data.pyvider_file_info.hosts_file.mime_type}",
    "",
    "/tmp directory:",
    "  Exists: ${data.pyvider_file_info.tmp_dir.exists}",
    "  Type: ${data.pyvider_file_info.tmp_dir.is_file ? "File" : data.pyvider_file_info.tmp_dir.is_dir ? "Directory" : "Other"}",
    "  Permissions: ${data.pyvider_file_info.tmp_dir.permissions}",
    "  Owner: ${data.pyvider_file_info.tmp_dir.owner}",
    "  Group: ${data.pyvider_file_info.tmp_dir.group}",
    "",
    "=== Application Config ===",
    "/etc/myapp/config.yaml:",
    "  Exists: ${data.pyvider_file_info.config_file.exists}",
    data.pyvider_file_info.config_file.exists ? "  Size: ${data.pyvider_file_info.config_file.size} bytes" : "  (File not found)",
    data.pyvider_file_info.config_file.exists ? "  Modified: ${data.pyvider_file_info.config_file.modified_time}" : "",
    "",
    "=== Current Directory ===",
    "Current working directory (.):",
    "  Exists: ${data.pyvider_file_info.current_dir.exists}",
    "  Type: ${data.pyvider_file_info.current_dir.is_dir ? "Directory" : "Not Directory"}",
    "  Permissions: ${data.pyvider_file_info.current_dir.permissions}",
    "",
    "=== Created Test Files ===",
    "Test directory (${pyvider_local_directory.test_dir.path}):",
    "  Exists: ${data.pyvider_file_info.created_dir.exists}",
    "  Type: Directory",
    "  Permissions: ${data.pyvider_file_info.created_dir.permissions}",
    "",
    "Sample text file:",
    "  Path: ${data.pyvider_file_info.created_text.path}",
    "  Exists: ${data.pyvider_file_info.created_text.exists}",
    "  Size: ${data.pyvider_file_info.created_text.size} bytes",
    "  MIME Type: ${data.pyvider_file_info.created_text.mime_type}",
    "  Modified: ${data.pyvider_file_info.created_text.modified_time}",
    "",
    "Sample JSON file:",
    "  Path: ${data.pyvider_file_info.created_json.path}",
    "  Exists: ${data.pyvider_file_info.created_json.exists}",
    "  Size: ${data.pyvider_file_info.created_json.size} bytes",
    "  MIME Type: ${data.pyvider_file_info.created_json.mime_type}",
    "  Modified: ${data.pyvider_file_info.created_json.modified_time}",
    "",
    "=== File Size Analysis ===",
    "Text file size: ${data.pyvider_file_info.created_text.size} bytes",
    "JSON file size: ${data.pyvider_file_info.created_json.size} bytes",
    "Larger file: ${data.pyvider_file_info.created_text.size > data.pyvider_file_info.created_json.size ? "text" : "json"}",
    "",
    "Report generated at: ${timestamp()}"
  ])

  depends_on = [
    data.pyvider_file_info.created_text,
    data.pyvider_file_info.created_json,
    data.pyvider_file_info.created_dir
  ]
}

# Calculate some basic statistics
locals {
  file_stats = {
    total_files_checked = 6
    existing_files = length([
      for info in [
        data.pyvider_file_info.hosts_file,
        data.pyvider_file_info.tmp_dir,
        data.pyvider_file_info.config_file,
        data.pyvider_file_info.current_dir,
        data.pyvider_file_info.created_text,
        data.pyvider_file_info.created_json
      ] : info if info.exists
    ])

    total_size_bytes = (
      data.pyvider_file_info.hosts_file.size +
      data.pyvider_file_info.created_text.size +
      data.pyvider_file_info.created_json.size
    )

    file_types = {
      regular_files = length([
        for info in [
          data.pyvider_file_info.hosts_file,
          data.pyvider_file_info.created_text,
          data.pyvider_file_info.created_json
        ] : info if info.is_file && info.exists
      ])

      directories = length([
        for info in [
          data.pyvider_file_info.tmp_dir,
          data.pyvider_file_info.current_dir,
          data.pyvider_file_info.created_dir
        ] : info if info.is_dir && info.exists
      ])
    }
  }
}

output "basic_file_info" {
  description = "Basic file information examples"
  value = {
    system_files = {
      hosts_file = {
        exists = data.pyvider_file_info.hosts_file.exists
        size = data.pyvider_file_info.hosts_file.size
        type = data.pyvider_file_info.hosts_file.is_file ? "file" : "other"
        permissions = data.pyvider_file_info.hosts_file.permissions
        mime_type = data.pyvider_file_info.hosts_file.mime_type
      }

      tmp_directory = {
        exists = data.pyvider_file_info.tmp_dir.exists
        is_directory = data.pyvider_file_info.tmp_dir.is_dir
        permissions = data.pyvider_file_info.tmp_dir.permissions
        owner = data.pyvider_file_info.tmp_dir.owner
      }
    }

    application_files = {
      config_exists = data.pyvider_file_info.config_file.exists
      current_dir_accessible = data.pyvider_file_info.current_dir.exists
    }

    created_files = {
      test_directory = {
        path = data.pyvider_file_info.created_dir.path
        exists = data.pyvider_file_info.created_dir.exists
        permissions = data.pyvider_file_info.created_dir.permissions
      }

      text_file = {
        path = data.pyvider_file_info.created_text.path
        exists = data.pyvider_file_info.created_text.exists
        size = data.pyvider_file_info.created_text.size
        mime_type = data.pyvider_file_info.created_text.mime_type
      }

      json_file = {
        path = data.pyvider_file_info.created_json.path
        exists = data.pyvider_file_info.created_json.exists
        size = data.pyvider_file_info.created_json.size
        mime_type = data.pyvider_file_info.created_json.mime_type
      }
    }

    statistics = local.file_stats

    report_file = pyvider_file_content.file_info_report.filename
  }
}