# Template-based configuration with dynamic content

# Read environment variables for the template
data "pyvider_env_variables" "app_vars" {
  keys = ["USER", "HOME", "HOSTNAME"]
}

# Create a configuration file using template functions
resource "pyvider_file_content" "app_properties" {
  filename = "/tmp/application.properties"
  content = join("\n", [
    "# Application Configuration",
    "# Generated on ${timestamp()}",
    "",
    "app.user=${lookup(data.pyvider_env_variables.app_vars.values, "USER", "unknown")}",
    "app.home=${lookup(data.pyvider_env_variables.app_vars.values, "HOME", "/tmp")}",
    "app.hostname=${lookup(data.pyvider_env_variables.app_vars.values, "HOSTNAME", "localhost")}",
    "",
    "# Database Configuration",
    "database.url=jdbc:postgresql://localhost:5432/myapp",
    "database.username=app_user",
    "database.pool.size=10",
    "",
    "# Feature Flags",
    "features.new_ui=true",
    "features.analytics=false"
  ])
}

# Create a shell script with executable content
resource "pyvider_file_content" "deploy_script" {
  filename = "/tmp/deploy.sh"
  content = templatefile("${path.module}/deploy.sh.tpl", {
    app_name = "my-terraform-app"
    version  = "1.0.0"
    user     = lookup(data.pyvider_env_variables.app_vars.values, "USER", "deploy")
  })
}

# Example template file content (this would be a separate .tpl file)
# #!/bin/bash
# set -e
#
# APP_NAME="${app_name}"
# VERSION="${version}"
# USER="${user}"
#
# echo "Deploying $APP_NAME version $VERSION as user $USER"
# echo "Timestamp: $(date)"
#
# # Add your deployment logic here
# echo "Deployment complete!"

output "template_outputs" {
  description = "Information about template-generated files"
  value = {
    properties_file = {
      path = pyvider_file_content.app_properties.filename
      hash = pyvider_file_content.app_properties.content_hash
    }
    deploy_script = {
      path = pyvider_file_content.deploy_script.filename
      hash = pyvider_file_content.deploy_script.content_hash
    }
  }
}