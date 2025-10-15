# Complete workspace setup for different development scenarios

variable "workspace_name" {
  description = "Name of the workspace to create"
  type        = string
  default     = "dev-workspace"
}

variable "workspace_type" {
  description = "Type of workspace: web, api, data, or fullstack"
  type        = string
  default     = "fullstack"
  validation {
    condition     = contains(["web", "api", "data", "fullstack"], var.workspace_type)
    error_message = "Workspace type must be one of: web, api, data, fullstack."
  }
}

data "pyvider_env_variables" "user_info" {
  keys = ["USER", "HOME"]
}

locals {
  workspace_root = "/tmp/workspaces/${var.workspace_name}"
  username = lookup(data.pyvider_env_variables.user_info.values, "USER", "developer")

  # Define workspace structures based on type
  workspace_configs = {
    web = {
      directories = ["src", "public", "assets", "styles", "scripts", "tests", "dist", "docs"]
      files = {
        "package.json" = {
          name         = var.workspace_name
          version      = "1.0.0"
          main         = "src/index.js"
          scripts = {
            start = "npm run dev"
            dev   = "webpack serve --mode development"
            build = "webpack --mode production"
            test  = "jest"
          }
        }
        "webpack.config.js" = "// Webpack configuration for ${var.workspace_name}"
        ".gitignore" = join("\n", [
          "node_modules/", "dist/", "*.log", ".env*", ".DS_Store"
        ])
      }
    }
    api = {
      directories = ["src", "controllers", "models", "routes", "middleware", "tests", "docs", "config", "logs"]
      files = {
        "package.json" = {
          name    = var.workspace_name
          version = "1.0.0"
          main    = "src/server.js"
          scripts = {
            start = "node src/server.js"
            dev   = "nodemon src/server.js"
            test  = "jest"
          }
        }
        "src/server.js" = "// Express server for ${var.workspace_name}"
        ".env.example" = join("\n", [
          "PORT=3000", "DATABASE_URL=postgresql://localhost:5432/${var.workspace_name}",
          "JWT_SECRET=your-secret-key", "NODE_ENV=development"
        ])
      }
    }
    data = {
      directories = ["notebooks", "data/raw", "data/processed", "data/external", "models", "reports", "scripts", "tests"]
      files = {
        "requirements.txt" = join("\n", [
          "pandas>=1.5.0", "numpy>=1.24.0", "matplotlib>=3.6.0",
          "seaborn>=0.12.0", "scikit-learn>=1.2.0", "jupyter>=1.0.0"
        ])
        "README.md" = "# ${var.workspace_name}\n\nData science workspace created with Terraform."
        ".gitignore" = join("\n", [
          "*.csv", "*.parquet", "__pycache__/", ".ipynb_checkpoints/",
          "data/raw/*", "!data/raw/.gitkeep", "models/*.pkl"
        ])
      }
    }
    fullstack = {
      directories = [
        "frontend/src", "frontend/public", "frontend/tests",
        "backend/src", "backend/tests", "backend/config",
        "database/migrations", "database/seeds",
        "docs", "scripts", "docker", "k8s"
      ]
      files = {
        "docker-compose.yml" = "# Docker Compose for ${var.workspace_name}"
        "README.md" = "# ${var.workspace_name}\n\nFullstack application workspace."
        ".env.example" = join("\n", [
          "# Frontend", "REACT_APP_API_URL=http://localhost:3001",
          "# Backend", "PORT=3001", "DATABASE_URL=postgresql://localhost:5432/${var.workspace_name}",
          "# Docker", "POSTGRES_DB=${var.workspace_name}", "POSTGRES_USER=dev", "POSTGRES_PASSWORD=devpass"
        ])
      }
    }
  }

  config = local.workspace_configs[var.workspace_type]
}

# Create workspace root
resource "pyvider_local_directory" "workspace_root" {
  path        = local.workspace_root
  permissions = "0o755"
}

# Create all directories for the workspace type
resource "pyvider_local_directory" "workspace_dirs" {
  for_each = toset(local.config.directories)

  path = "${local.workspace_root}/${each.value}"
  depends_on = [pyvider_local_directory.workspace_root]
}

# Create workspace-specific configuration files
resource "pyvider_file_content" "workspace_files" {
  for_each = local.config.files

  filename = "${pyvider_local_directory.workspace_root.path}/${each.key}"
  content = can(jsondecode(jsonencode(each.value))) && length(regexall("\\{|\\[", jsonencode(each.value))) > 0 ?
    jsonencode(each.value) : each.value

  depends_on = [pyvider_local_directory.workspace_root]
}

# Create common development files
resource "pyvider_file_content" "workspace_readme" {
  filename = "${pyvider_local_directory.workspace_root.path}/WORKSPACE_INFO.md"
  content = <<-EOF
    # ${var.workspace_name}

    **Type:** ${var.workspace_type}
    **Created:** ${timestamp()}
    **Owner:** ${local.username}

    ## Workspace Structure

    This ${var.workspace_type} workspace includes the following directories:

    ${join("\n", [for dir in local.config.directories : "- `${dir}/`"])}

    ## Getting Started

    1. Navigate to the workspace:
       ```bash
       cd ${local.workspace_root}
       ```

    2. Follow the setup instructions for your workspace type.

    ## Workspace Type: ${upper(var.workspace_type)}

    ${var.workspace_type == "web" ? "This is a frontend web development workspace with webpack configuration." : ""}
    ${var.workspace_type == "api" ? "This is a backend API development workspace with Express.js setup." : ""}
    ${var.workspace_type == "data" ? "This is a data science workspace with Python and Jupyter setup." : ""}
    ${var.workspace_type == "fullstack" ? "This is a fullstack development workspace with frontend, backend, and database components." : ""}

    ## Directory Permissions

    ${join("\n", [for dir_name, dir_resource in pyvider_local_directory.workspace_dirs :
      "- `${dir_name}`: ${dir_resource.permissions != null ? dir_resource.permissions : "default (0o755)"}"
    ])}

    ## File Count Monitoring

    ${join("\n", [for dir_name, dir_resource in pyvider_local_directory.workspace_dirs :
      "- `${dir_name}`: ${dir_resource.file_count} items"
    ])}
  EOF

  depends_on = [pyvider_local_directory.workspace_dirs]
}

# Create development helper scripts
resource "pyvider_local_directory" "scripts_dir" {
  path = "${local.workspace_root}/scripts"
  depends_on = [pyvider_local_directory.workspace_root]
}

resource "pyvider_file_content" "setup_script" {
  filename = "${pyvider_local_directory.scripts_dir.path}/setup.sh"
  content = <<-EOF
    #!/bin/bash
    set -e

    echo "Setting up ${var.workspace_name} (${var.workspace_type}) workspace..."

    # Navigate to workspace root
    cd "${local.workspace_root}"

    ${var.workspace_type == "web" || var.workspace_type == "fullstack" ? "echo 'Installing Node.js dependencies...'\nif [ -f package.json ]; then\n    npm install\nfi" : ""}

    ${var.workspace_type == "data" ? "echo 'Setting up Python environment...'\nif [ -f requirements.txt ]; then\n    pip install -r requirements.txt\nfi" : ""}

    ${var.workspace_type == "api" || var.workspace_type == "fullstack" ? "echo 'Setting up API environment...'\nif [ -f .env.example ]; then\n    cp .env.example .env\n    echo 'Created .env file from example'\nfi" : ""}

    echo "Workspace setup complete!"
    echo "Workspace location: ${local.workspace_root}"
    echo "Type: ${var.workspace_type}"
    echo "Created by: ${local.username}"
  EOF

  depends_on = [pyvider_local_directory.scripts_dir]
}

resource "pyvider_file_content" "cleanup_script" {
  filename = "${pyvider_local_directory.scripts_dir.path}/cleanup.sh"
  content = <<-EOF
    #!/bin/bash

    echo "Cleaning up ${var.workspace_name} workspace..."

    # Navigate to workspace root
    cd "${local.workspace_root}"

    # Clean common temporary files
    find . -name "*.log" -delete
    find . -name "*.tmp" -delete
    find . -name ".DS_Store" -delete

    ${var.workspace_type == "web" || var.workspace_type == "fullstack" ? "# Clean Node.js artifacts\nrm -rf node_modules/\nrm -rf dist/\nrm -rf build/" : ""}

    ${var.workspace_type == "data" ? "# Clean Python artifacts\nfind . -name '__pycache__' -type d -exec rm -rf {} +\nfind . -name '*.pyc' -delete\nrm -rf .ipynb_checkpoints/" : ""}

    ${var.workspace_type == "api" || var.workspace_type == "fullstack" ? "# Clean API artifacts\nrm -rf logs/*.log\nrm -f .env" : ""}

    echo "Cleanup complete!"
  EOF

  depends_on = [pyvider_local_directory.scripts_dir]
}

output "workspace_setup" {
  description = "Complete workspace setup information"
  value = {
    workspace_name = var.workspace_name
    workspace_type = var.workspace_type
    workspace_root = pyvider_local_directory.workspace_root.path
    created_by     = local.username

    structure = {
      directories = {
        for dir_name, dir_resource in pyvider_local_directory.workspace_dirs :
        dir_name => {
          path        = dir_resource.path
          file_count  = dir_resource.file_count
          permissions = dir_resource.permissions
        }
      }
      root_file_count = pyvider_local_directory.workspace_root.file_count
    }

    created_files = [for filename in keys(local.config.files) : filename]

    quick_start = {
      setup_command   = "cd ${local.workspace_root} && bash scripts/setup.sh"
      cleanup_command = "cd ${local.workspace_root} && bash scripts/cleanup.sh"
      workspace_info  = "${local.workspace_root}/WORKSPACE_INFO.md"
    }

    type_specific_info = {
      web = var.workspace_type == "web" ? {
        main_directory = "${local.workspace_root}/src"
        public_assets  = "${local.workspace_root}/public"
        build_output   = "${local.workspace_root}/dist"
      } : null

      api = var.workspace_type == "api" ? {
        server_file    = "${local.workspace_root}/src/server.js"
        routes_dir     = "${local.workspace_root}/routes"
        config_dir     = "${local.workspace_root}/config"
      } : null

      data = var.workspace_type == "data" ? {
        notebooks_dir  = "${local.workspace_root}/notebooks"
        raw_data_dir   = "${local.workspace_root}/data/raw"
        processed_dir  = "${local.workspace_root}/data/processed"
      } : null

      fullstack = var.workspace_type == "fullstack" ? {
        frontend_dir = "${local.workspace_root}/frontend"
        backend_dir  = "${local.workspace_root}/backend"
        database_dir = "${local.workspace_root}/database"
      } : null
    }
  }
}