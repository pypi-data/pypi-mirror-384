# Create a complete project directory structure

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "my-terraform-project"
}

variable "base_path" {
  description = "Base path for project creation"
  type        = string
  default     = "/tmp"
}

locals {
  project_root = "${var.base_path}/${var.project_name}"
}

# Create project root directory
resource "pyvider_local_directory" "project_root" {
  path        = local.project_root
  permissions = "0o755"
}

# Source code directories
resource "pyvider_local_directory" "src" {
  path = "${local.project_root}/src"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "src_components" {
  path = "${local.project_root}/src/components"
  depends_on = [pyvider_local_directory.src]
}

resource "pyvider_local_directory" "src_utils" {
  path = "${local.project_root}/src/utils"
  depends_on = [pyvider_local_directory.src]
}

# Test directories
resource "pyvider_local_directory" "tests" {
  path = "${local.project_root}/tests"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "tests_unit" {
  path = "${local.project_root}/tests/unit"
  depends_on = [pyvider_local_directory.tests]
}

resource "pyvider_local_directory" "tests_integration" {
  path = "${local.project_root}/tests/integration"
  depends_on = [pyvider_local_directory.tests]
}

# Documentation directories
resource "pyvider_local_directory" "docs" {
  path        = "${local.project_root}/docs"
  permissions = "0o755"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "docs_api" {
  path = "${local.project_root}/docs/api"
  depends_on = [pyvider_local_directory.docs]
}

# Configuration directories
resource "pyvider_local_directory" "config" {
  path        = "${local.project_root}/config"
  permissions = "0o750"  # More restrictive for config
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "config_environments" {
  path = "${local.project_root}/config/environments"
  depends_on = [pyvider_local_directory.config]
}

# Runtime directories
resource "pyvider_local_directory" "logs" {
  path        = "${local.project_root}/logs"
  permissions = "0o755"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "tmp" {
  path        = "${local.project_root}/tmp"
  permissions = "0o777"  # World writable for temp files
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "data" {
  path        = "${local.project_root}/data"
  permissions = "0o750"  # Restrictive for data
  depends_on = [pyvider_local_directory.project_root]
}

# Development-specific directories
resource "pyvider_local_directory" "scripts" {
  path = "${local.project_root}/scripts"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "tools" {
  path = "${local.project_root}/tools"
  depends_on = [pyvider_local_directory.project_root]
}

# Create essential project files
resource "pyvider_file_content" "readme" {
  filename = "${pyvider_local_directory.project_root.path}/README.md"
  content = <<-EOF
    # ${var.project_name}

    A project created with Terraform and Pyvider Components.

    ## Directory Structure

    ```
    ${var.project_name}/
    ├── src/                 # Source code
    │   ├── components/      # Reusable components
    │   └── utils/          # Utility functions
    ├── tests/              # Test files
    │   ├── unit/           # Unit tests
    │   └── integration/    # Integration tests
    ├── docs/               # Documentation
    │   └── api/            # API documentation
    ├── config/             # Configuration files
    │   └── environments/   # Environment-specific configs
    ├── logs/               # Log files
    ├── tmp/                # Temporary files
    ├── data/               # Application data
    ├── scripts/            # Build/deployment scripts
    └── tools/              # Development tools
    ```

    ## Getting Started

    1. Navigate to the project directory:
       ```bash
       cd ${local.project_root}
       ```

    2. Start development!

    Generated on: ${timestamp()}
  EOF

  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_file_content" "gitignore" {
  filename = "${pyvider_local_directory.project_root.path}/.gitignore"
  content = <<-EOF
    # Logs
    logs/
    *.log

    # Temporary files
    tmp/
    *.tmp
    *.temp

    # OS generated files
    .DS_Store
    .DS_Store?
    ._*
    .Spotlight-V100
    .Trashes
    ehthumbs.db
    Thumbs.db

    # IDE files
    .vscode/
    .idea/
    *.swp
    *.swo

    # Environment files
    .env
    .env.local
    .env.*.local

    # Dependency directories
    node_modules/
    __pycache__/
    .pytest_cache/
  EOF

  depends_on = [pyvider_local_directory.project_root]
}

# Create environment configuration files
resource "pyvider_file_content" "env_development" {
  filename = "${pyvider_local_directory.config_environments.path}/development.conf"
  content = <<-EOF
    # Development Environment Configuration
    DEBUG=true
    LOG_LEVEL=debug
    DATABASE_URL=sqlite:///tmp/dev.db
    CACHE_ENABLED=false
  EOF

  depends_on = [pyvider_local_directory.config_environments]
}

resource "pyvider_file_content" "env_production" {
  filename = "${pyvider_local_directory.config_environments.path}/production.conf"
  content = <<-EOF
    # Production Environment Configuration
    DEBUG=false
    LOG_LEVEL=info
    DATABASE_URL=postgresql://localhost:5432/app_prod
    CACHE_ENABLED=true
    CACHE_TTL=3600
  EOF

  depends_on = [pyvider_local_directory.config_environments]
}

output "project_structure" {
  description = "Complete project directory structure"
  value = {
    project_name = var.project_name
    project_root = pyvider_local_directory.project_root.path

    directories = {
      source = {
        path       = pyvider_local_directory.src.path
        components = pyvider_local_directory.src_components.path
        utils      = pyvider_local_directory.src_utils.path
      }
      tests = {
        path        = pyvider_local_directory.tests.path
        unit        = pyvider_local_directory.tests_unit.path
        integration = pyvider_local_directory.tests_integration.path
      }
      docs = {
        path = pyvider_local_directory.docs.path
        api  = pyvider_local_directory.docs_api.path
      }
      config = {
        path         = pyvider_local_directory.config.path
        permissions  = pyvider_local_directory.config.permissions
        environments = pyvider_local_directory.config_environments.path
      }
      runtime = {
        logs = {
          path        = pyvider_local_directory.logs.path
          permissions = pyvider_local_directory.logs.permissions
        }
        tmp = {
          path        = pyvider_local_directory.tmp.path
          permissions = pyvider_local_directory.tmp.permissions
        }
        data = {
          path        = pyvider_local_directory.data.path
          permissions = pyvider_local_directory.data.permissions
        }
      }
      development = {
        scripts = pyvider_local_directory.scripts.path
        tools   = pyvider_local_directory.tools.path
      }
    }

    file_counts = {
      root   = pyvider_local_directory.project_root.file_count
      config = pyvider_local_directory.config_environments.file_count
      src    = pyvider_local_directory.src.file_count
      tests  = pyvider_local_directory.tests.file_count
    }
  }
}