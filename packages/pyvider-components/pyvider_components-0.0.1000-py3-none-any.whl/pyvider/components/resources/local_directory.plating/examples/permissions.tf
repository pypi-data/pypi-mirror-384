# Permission management examples with different security levels

# Public directory - world readable/executable
resource "pyvider_local_directory" "public_files" {
  path        = "/tmp/public"
  permissions = "0o755"  # rwxr-xr-x
}

# Private user directory - only owner access
resource "pyvider_local_directory" "private_user" {
  path        = "/tmp/private_user"
  permissions = "0o700"  # rwx------
}

# Group shared directory - owner and group access
resource "pyvider_local_directory" "group_shared" {
  path        = "/tmp/group_shared"
  permissions = "0o750"  # rwxr-x---
}

# Read-only shared directory - owner write, others read
resource "pyvider_local_directory" "readonly_shared" {
  path        = "/tmp/readonly_shared"
  permissions = "0o744"  # rwxr--r--
}

# Secure configuration directory - restrictive permissions
resource "pyvider_local_directory" "secure_config" {
  path        = "/tmp/secure_config"
  permissions = "0o700"  # rwx------
}

# Web server directory - appropriate for web content
resource "pyvider_local_directory" "web_content" {
  path        = "/tmp/web"
  permissions = "0o755"  # rwxr-xr-x
}

# Log directory - allowing group write for log rotation
resource "pyvider_local_directory" "logs_group_write" {
  path        = "/tmp/logs_shared"
  permissions = "0o775"  # rwxrwxr-x
}

# Temporary directory - world writable (use with caution)
resource "pyvider_local_directory" "temp_world" {
  path        = "/tmp/temp_world"
  permissions = "0o777"  # rwxrwxrwx
}

# Create files with different permissions to demonstrate
resource "pyvider_file_content" "public_readme" {
  filename = "${pyvider_local_directory.public_files.path}/README.txt"
  content  = "This is a public file that anyone can read."

  depends_on = [pyvider_local_directory.public_files]
}

resource "pyvider_file_content" "private_secret" {
  filename = "${pyvider_local_directory.private_user.path}/secret.txt"
  content  = "This is a private file only the owner can access."

  depends_on = [pyvider_local_directory.private_user]
}

resource "pyvider_file_content" "group_config" {
  filename = "${pyvider_local_directory.group_shared.path}/team_config.yml"
  content = <<-EOF
    # Team Configuration
    team_name: "DevOps Team"
    members:
      - alice
      - bob
      - charlie

    shared_resources:
      - database: "team_db"
      - cache: "redis_cluster"

    permissions:
      read: ["team_members", "managers"]
      write: ["team_leads", "managers"]
  EOF

  depends_on = [pyvider_local_directory.group_shared]
}

resource "pyvider_file_content" "web_index" {
  filename = "${pyvider_local_directory.web_content.path}/index.html"
  content = <<-EOF
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Web Page</title>
    </head>
    <body>
        <h1>Welcome to the Sample Site</h1>
        <p>This directory has web-appropriate permissions (0o755).</p>
        <p>Generated at: ${timestamp()}</p>
    </body>
    </html>
  EOF

  depends_on = [pyvider_local_directory.web_content]
}

resource "pyvider_file_content" "secure_credentials" {
  filename = "${pyvider_local_directory.secure_config.path}/credentials.json"
  content = jsonencode({
    database = {
      username = "app_user"
      password = "secure_password_here"
      host     = "db.internal.example.com"
    }
    api_keys = {
      third_party_service = "api_key_12345"
      payment_gateway     = "pk_live_abcdef123456"
    }
    encryption = {
      secret_key = "very_secret_encryption_key"
      salt       = "random_salt_value"
    }
  })

  depends_on = [pyvider_local_directory.secure_config]
}

# Demonstrate permission checking with a simple script
resource "pyvider_file_content" "permission_checker" {
  filename = "${pyvider_local_directory.public_files.path}/check_permissions.sh"
  content = <<-EOF
    #!/bin/bash

    echo "=== Directory Permission Check ==="
    echo

    for dir in "/tmp/public" "/tmp/private_user" "/tmp/group_shared" "/tmp/secure_config"; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            ls -ld "$dir"
            echo "Permissions: $(stat -c '%a' "$dir" 2>/dev/null || stat -f '%A' "$dir" 2>/dev/null)"
            echo
        fi
    done

    echo "=== File Permission Check ==="
    echo

    find /tmp -maxdepth 2 -name "*.txt" -o -name "*.json" -o -name "*.yml" 2>/dev/null | while read file; do
        if [ -f "$file" ]; then
            echo "File: $file"
            ls -l "$file"
            echo
        fi
    done
  EOF

  depends_on = [pyvider_local_directory.public_files]
}

output "permission_examples" {
  description = "Directory permission examples and their meanings"
  value = {
    directories = {
      public = {
        path        = pyvider_local_directory.public_files.path
        permissions = pyvider_local_directory.public_files.permissions
        meaning     = "rwxr-xr-x - Owner: read/write/execute, Group/Others: read/execute"
        use_case    = "Public files, documentation, web content"
      }
      private_user = {
        path        = pyvider_local_directory.private_user.path
        permissions = pyvider_local_directory.private_user.permissions
        meaning     = "rwx------ - Owner: read/write/execute, Others: no access"
        use_case    = "Personal files, private keys, user-specific config"
      }
      group_shared = {
        path        = pyvider_local_directory.group_shared.path
        permissions = pyvider_local_directory.group_shared.permissions
        meaning     = "rwxr-x--- - Owner: read/write/execute, Group: read/execute, Others: no access"
        use_case    = "Team shared files, project directories"
      }
      secure_config = {
        path        = pyvider_local_directory.secure_config.path
        permissions = pyvider_local_directory.secure_config.permissions
        meaning     = "rwx------ - Owner only access"
        use_case    = "Credentials, secrets, sensitive configuration"
      }
      web_content = {
        path        = pyvider_local_directory.web_content.path
        permissions = pyvider_local_directory.web_content.permissions
        meaning     = "rwxr-xr-x - Standard web server permissions"
        use_case    = "Web server document root, static assets"
      }
      logs_group_write = {
        path        = pyvider_local_directory.logs_group_write.path
        permissions = pyvider_local_directory.logs_group_write.permissions
        meaning     = "rwxrwxr-x - Owner/Group: read/write/execute, Others: read/execute"
        use_case    = "Shared log directories with log rotation"
      }
      temp_world = {
        path        = pyvider_local_directory.temp_world.path
        permissions = pyvider_local_directory.temp_world.permissions
        meaning     = "rwxrwxrwx - World writable (use with extreme caution)"
        use_case    = "Temporary directories for inter-process communication"
      }
    }

    security_best_practices = {
      principle_of_least_privilege = "Grant only the minimum permissions necessary"
      avoid_world_writable         = "0o777 permissions are dangerous and should be avoided"
      separate_config_and_data     = "Use different permission levels for config vs data directories"
      regular_audits              = "Periodically review directory permissions"
    }

    permission_guide = {
      "0o700" = "Private - Owner only"
      "0o750" = "Group shared - Owner full, Group read/execute"
      "0o755" = "Public read - Standard directory permissions"
      "0o775" = "Group writable - Shared write access"
      "0o777" = "World writable - Dangerous, avoid in production"
    }
  }
}