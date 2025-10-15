# Basic file creation and management
resource "pyvider_file_content" "readme" {
  filename = "/tmp/pyvider_readme.txt"
  content  = "Welcome to Pyvider Components!\n\nThis file was created by Terraform."
}

# Show the computed attributes
output "file_details" {
  description = "Details about the created file"
  value = {
    filename     = pyvider_file_content.readme.filename
    exists       = pyvider_file_content.readme.exists
    content_hash = pyvider_file_content.readme.content_hash
    content_size = length(pyvider_file_content.readme.content)
  }
}

# Create a simple JSON configuration file
resource "pyvider_file_content" "json_config" {
  filename = "/tmp/app_config.json"
  content = jsonencode({
    app_name = "my-terraform-app"
    version  = "1.0.0"
    debug    = false
    database = {
      host = "localhost"
      port = 5432
    }
  })
}

output "json_config_hash" {
  description = "Hash of the JSON configuration file"
  value       = pyvider_file_content.json_config.content_hash
}