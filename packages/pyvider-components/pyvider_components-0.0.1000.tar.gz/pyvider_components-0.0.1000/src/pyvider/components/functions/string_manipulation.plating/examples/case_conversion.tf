# Case conversion function examples

# Basic case conversion examples
locals {
  original_texts = [
    "user_profile_settings",
    "APIEndpointHandler",
    "database-connection-pool",
    "My Application Title",
    "SYSTEM_CONFIG_VALUE"
  ]

  # Convert to snake_case
  snake_case_results = [
    for text in local.original_texts :
    provider::pyvider::to_snake_case(text)
  ]
  # Results: ["user_profile_settings", "api_endpoint_handler", "database_connection_pool", "my_application_title", "system_config_value"]

  # Convert to camelCase
  camel_case_results = [
    for text in local.original_texts :
    provider::pyvider::to_camel_case(text)
  ]
  # Results: ["userProfileSettings", "apiEndpointHandler", "databaseConnectionPool", "myApplicationTitle", "systemConfigValue"]

  # Convert to PascalCase
  pascal_case_results = [
    for text in local.original_texts :
    provider::pyvider::to_camel_case(text, true)
  ]
  # Results: ["UserProfileSettings", "ApiEndpointHandler", "DatabaseConnectionPool", "MyApplicationTitle", "SystemConfigValue"]

  # Convert to kebab-case
  kebab_case_results = [
    for text in local.original_texts :
    provider::pyvider::to_kebab_case(text)
  ]
  # Results: ["user-profile-settings", "api-endpoint-handler", "database-connection-pool", "my-application-title", "system-config-value"]
}

# Database to API field mapping
variable "database_fields" {
  type = list(string)
  default = [
    "user_id",
    "first_name",
    "last_name",
    "email_address",
    "phone_number",
    "created_at",
    "updated_at",
    "is_active",
    "last_login_time"
  ]
}

locals {
  # Create API field mappings
  api_field_mapping = {
    for field in var.database_fields :
    field => provider::pyvider::to_camel_case(field)
  }

  # Generate JavaScript object
  js_object_fields = [
    for db_field, api_field in local.api_field_mapping :
    "  ${api_field}: data.${db_field}"
  ]

  js_mapping_code = "const apiResponse = {\n${join(",\n", local.js_object_fields)}\n};"
}

# URL slug generation
variable "page_titles" {
  type = list(string)
  default = [
    "Getting Started with Terraform",
    "Advanced Provider Development Guide",
    "Best Practices & Common Patterns",
    "Troubleshooting Configuration Issues",
    "API Reference Documentation"
  ]
}

locals {
  # Generate URL-friendly slugs
  url_slugs = {
    for title in var.page_titles :
    title => provider::pyvider::to_kebab_case(title)
  }

  # Create navigation links
  navigation_links = [
    for title, slug in local.url_slugs :
    {
      title = title
      slug = slug
      url = "/docs/${slug}"
    }
  ]
}

# CSS class generation
variable "ui_components" {
  type = list(object({
    name = string
    type = string
  }))
  default = [
    { name = "userProfileCard", type = "component" },
    { name = "navigationMenubar", type = "layout" },
    { name = "searchInputField", type = "form" },
    { name = "dataTableContainer", type = "container" },
    { name = "modalDialogWindow", type = "overlay" }
  ]
}

locals {
  # Generate CSS classes
  css_classes = {
    for component in var.ui_components :
    component.name => {
      class_name = provider::pyvider::to_kebab_case(component.name)
      full_class = "${provider::pyvider::to_kebab_case(component.type)}-${provider::pyvider::to_kebab_case(component.name)}"
      type = component.type
    }
  }
}

# Configuration key normalization
variable "app_settings" {
  type = map(any)
  default = {
    "Database Host" = "localhost"
    "API Base URL" = "https://api.example.com"
    "Cache Timeout (seconds)" = 300
    "Debug Mode Enabled" = false
    "Max Connection Pool Size" = 20
  }
}

locals {
  # Normalize to different naming conventions
  snake_case_config = {
    for display_name, value in var.app_settings :
    provider::pyvider::to_snake_case(display_name) => value
  }

  camel_case_config = {
    for display_name, value in var.app_settings :
    provider::pyvider::to_camel_case(display_name) => value
  }

  kebab_case_config = {
    for display_name, value in var.app_settings :
    provider::pyvider::to_kebab_case(display_name) => value
  }
}

# File naming patterns
variable "document_info" {
  type = list(object({
    title = string
    category = string
    version = string
  }))
  default = [
    {
      title = "User Manual"
      category = "Documentation"
      version = "2.1"
    },
    {
      title = "API Reference Guide"
      category = "Technical Documentation"
      version = "1.0"
    },
    {
      title = "Installation Instructions"
      category = "Setup Guide"
      version = "3.2"
    }
  ]
}

locals {
  # Generate various filename patterns
  document_files = [
    for doc in var.document_info : {
      # Snake case filename
      snake_file = "${provider::pyvider::to_snake_case(doc.title)}_v${replace(doc.version, ".", "_")}.md"

      # Kebab case filename
      kebab_file = "${provider::pyvider::to_kebab_case(doc.title)}-v${replace(doc.version, ".", "-")}.html"

      # Category-based organization
      category_path = "${provider::pyvider::to_snake_case(doc.category)}/${provider::pyvider::to_kebab_case(doc.title)}"

      original = doc
    }
  ]
}

# Environment variable generation
variable "service_config" {
  type = map(string)
  default = {
    "Database Connection String" = "postgresql://localhost:5432/mydb"
    "Redis Cache URL" = "redis://localhost:6379"
    "API Service Port" = "8080"
    "Log Level Setting" = "INFO"
    "JWT Secret Key" = "your-secret-key"
  }
}

locals {
  # Convert to environment variable format (UPPER_SNAKE_CASE)
  env_variables = {
    for config_name, value in var.service_config :
    provider::pyvider::upper(provider::pyvider::to_snake_case(config_name)) => value
  }

  # Generate .env file content
  env_file_lines = [
    for env_name, value in local.env_variables :
    "${env_name}=${value}"
  ]
}

# Create output files
resource "pyvider_file_content" "case_conversion_examples" {
  filename = "/tmp/case_conversion_examples.txt"
  content = join("\n", [
    "=== Case Conversion Examples ===",
    "",
    "Original texts:",
    join("\n", [for i, text in local.original_texts : "  ${i + 1}. ${text}"]),
    "",
    "Snake case results:",
    join("\n", [for i, result in local.snake_case_results : "  ${i + 1}. ${result}"]),
    "",
    "Camel case results:",
    join("\n", [for i, result in local.camel_case_results : "  ${i + 1}. ${result}"]),
    "",
    "Pascal case results:",
    join("\n", [for i, result in local.pascal_case_results : "  ${i + 1}. ${result}"]),
    "",
    "Kebab case results:",
    join("\n", [for i, result in local.kebab_case_results : "  ${i + 1}. ${result}"])
  ])
}

resource "pyvider_file_content" "javascript_mapping" {
  filename = "/tmp/api_field_mapping.js"
  content = join("\n", [
    "// Database to API field mapping",
    "// Generated from Terraform configuration",
    "",
    local.js_mapping_code,
    "",
    "// Field mapping reference:",
    join("\n", [
      for db_field, api_field in local.api_field_mapping :
      "// ${db_field} -> ${api_field}"
    ])
  ])
}

resource "pyvider_file_content" "css_classes" {
  filename = "/tmp/component_styles.css"
  content = join("\n", concat(
    ["/* Component CSS Classes */", "/* Generated from UI component definitions */", ""],
    flatten([
      for component_name, info in local.css_classes : [
        "/* ${component_name} (${info.type}) */",
        ".${info.class_name} {",
        "  /* Component styles for ${component_name} */",
        "}",
        "",
        ".${info.full_class} {",
        "  /* Specific ${info.type} styles for ${component_name} */",
        "}",
        ""
      ]
    ])
  ))
}

resource "pyvider_file_content" "navigation_config" {
  filename = "/tmp/navigation.json"
  content = jsonencode({
    title = "Documentation Navigation"
    links = local.navigation_links
    url_mapping = local.url_slugs
  })
}

resource "pyvider_file_content" "config_files" {
  filename = "/tmp/multi_format_config.json"
  content = jsonencode({
    snake_case = local.snake_case_config
    camelCase = local.camel_case_config
    "kebab-case" = local.kebab_case_config
  })
}

resource "pyvider_file_content" "environment_variables" {
  filename = "/tmp/service.env"
  content = join("\n", concat(
    ["# Service Environment Variables", "# Generated from configuration"],
    local.env_file_lines
  ))
}

# Output conversion results
output "case_conversion_results" {
  value = {
    conversion_examples = {
      original = local.original_texts
      snake_case = local.snake_case_results
      camel_case = local.camel_case_results
      pascal_case = local.pascal_case_results
      kebab_case = local.kebab_case_results
    }

    api_mapping = {
      total_fields = length(var.database_fields)
      field_mapping = local.api_field_mapping
      js_file = pyvider_file_content.javascript_mapping.filename
    }

    web_assets = {
      navigation_links = length(local.navigation_links)
      css_classes = length(local.css_classes)
      navigation_file = pyvider_file_content.navigation_config.filename
      css_file = pyvider_file_content.css_classes.filename
    }

    configuration = {
      formats_generated = 3
      config_file = pyvider_file_content.config_files.filename
      env_file = pyvider_file_content.environment_variables.filename
      env_variables = length(local.env_variables)
    }

    file_patterns = {
      documents_processed = length(local.document_files)
      pattern_examples = [for doc in local.document_files : {
        snake_file = doc.snake_file
        kebab_file = doc.kebab_file
        category_path = doc.category_path
      }]
    }
  }
}