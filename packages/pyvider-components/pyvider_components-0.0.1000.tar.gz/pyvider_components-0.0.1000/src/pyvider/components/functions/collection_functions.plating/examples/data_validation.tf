# Data validation examples using collection functions

# User input validation
variable "user_registrations" {
  type = list(object({
    username = string
    email    = string
    age      = optional(number)
    roles    = optional(list(string), [])
  }))
  default = [
    {
      username = "alice123"
      email    = "alice@example.com"
      age      = 30
      roles    = ["user", "moderator"]
    },
    {
      username = "bob456"
      email    = "bob@example.com"
      roles    = ["user"]
    },
    {
      username = "charlie789"
      email    = "charlie@test.com"
      age      = 25
    }
  ]
}

locals {
  # Define validation rules
  required_fields = ["username", "email"]
  valid_roles = ["user", "admin", "moderator", "guest"]
  min_username_length = 3
  max_username_length = 20

  # Validate each user registration
  validation_results = [
    for idx, user in var.user_registrations : {
      index = idx
      username = user.username
      email = user.email

      # Check required fields
      has_username = provider::pyvider::contains(user, "username") && provider::pyvider::length(user.username) > 0
      has_email = provider::pyvider::contains(user, "email") && provider::pyvider::length(user.email) > 0

      # Username validation
      username_length = provider::pyvider::length(user.username)
      username_valid_length = (
        local.username_length >= local.min_username_length &&
        local.username_length <= local.max_username_length
      )
      username_has_at_symbol = provider::pyvider::contains(user.username, "@")

      # Email validation (basic)
      email_has_at = provider::pyvider::contains(user.email, "@")
      email_has_dot = provider::pyvider::contains(user.email, ".")

      # Role validation
      invalid_roles = [
        for role in user.roles :
        role if !provider::pyvider::contains(local.valid_roles, role)
      ]
      has_invalid_roles = provider::pyvider::length(local.invalid_roles) > 0

      # Overall validation
      is_valid = (
        local.has_username &&
        local.has_email &&
        local.username_valid_length &&
        !local.username_has_at_symbol &&
        local.email_has_at &&
        local.email_has_dot &&
        !local.has_invalid_roles
      )

      # Collect all errors
      errors = concat(
        !local.has_username ? ["Missing username"] : [],
        !local.has_email ? ["Missing email"] : [],
        !local.username_valid_length ? ["Username length must be ${local.min_username_length}-${local.max_username_length} characters"] : [],
        local.username_has_at_symbol ? ["Username cannot contain @ symbol"] : [],
        !local.email_has_at ? ["Email must contain @ symbol"] : [],
        !local.email_has_dot ? ["Email must contain . symbol"] : [],
        local.has_invalid_roles ? ["Invalid roles: ${join(", ", local.invalid_roles)}"] : []
      )
    }
  ]

  # Summary statistics
  total_users = provider::pyvider::length(var.user_registrations)
  valid_users = [for result in local.validation_results : result if result.is_valid]
  invalid_users = [for result in local.validation_results : result if !result.is_valid]
  valid_count = provider::pyvider::length(local.valid_users)
  invalid_count = provider::pyvider::length(local.invalid_users)
}

# Configuration validation
variable "service_configs" {
  type = map(object({
    host     = string
    port     = number
    protocol = string
    ssl      = optional(bool, false)
    timeout  = optional(number, 30)
  }))
  default = {
    api = {
      host     = "api.example.com"
      port     = 8080
      protocol = "http"
      ssl      = true
      timeout  = 60
    }
    database = {
      host     = "db.example.com"
      port     = 5432
      protocol = "postgresql"
    }
    cache = {
      host     = "cache.example.com"
      port     = 6379
      protocol = "redis"
      timeout  = 10
    }
  }
}

locals {
  # Define validation rules for services
  valid_protocols = ["http", "https", "tcp", "postgresql", "mysql", "redis"]
  required_service_fields = ["host", "port", "protocol"]

  # Validate service configurations
  service_validation = {
    for service_name, config in var.service_configs : service_name => {
      # Check required fields
      missing_fields = [
        for field in local.required_service_fields :
        field if !provider::pyvider::contains(config, field)
      ]
      has_all_required = provider::pyvider::length(local.missing_fields) == 0

      # Validate protocol
      protocol_valid = provider::pyvider::contains(local.valid_protocols, config.protocol)

      # Validate SSL consistency
      ssl_protocol_mismatch = (
        provider::pyvider::lookup(config, "ssl", false) == true &&
        config.protocol == "http"
      )

      # Port range validation
      port_in_range = config.port >= 1 && config.port <= 65535

      # Overall validation
      is_valid = (
        local.has_all_required &&
        local.protocol_valid &&
        !local.ssl_protocol_mismatch &&
        local.port_in_range
      )

      # Collect errors
      errors = concat(
        provider::pyvider::length(local.missing_fields) > 0 ? ["Missing fields: ${join(", ", local.missing_fields)}"] : [],
        !local.protocol_valid ? ["Invalid protocol: ${config.protocol}"] : [],
        local.ssl_protocol_mismatch ? ["SSL enabled but protocol is HTTP"] : [],
        !local.port_in_range ? ["Port ${config.port} is out of valid range (1-65535)"] : []
      )
    }
  }

  # Service validation summary
  total_services = provider::pyvider::length(var.service_configs)
  valid_services = [
    for name, validation in local.service_validation :
    name if validation.is_valid
  ]
  invalid_services = [
    for name, validation in local.service_validation :
    name if !validation.is_valid
  ]
  valid_service_count = provider::pyvider::length(local.valid_services)
  invalid_service_count = provider::pyvider::length(local.invalid_services)
}

# API endpoint validation
variable "api_endpoints" {
  type = list(object({
    path   = string
    method = string
    auth   = optional(bool, true)
    public = optional(bool, false)
  }))
  default = [
    { path = "/users", method = "GET", auth = true },
    { path = "/users", method = "POST", auth = true },
    { path = "/health", method = "GET", auth = false, public = true },
    { path = "/admin/stats", method = "GET", auth = true },
    { path = "/public/info", method = "GET", auth = false, public = true },
    { path = "/invalid-path", method = "PATCH", auth = true }  # Invalid method for demo
  ]
}

locals {
  # Define API validation rules
  valid_http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
  admin_paths = ["/admin", "/management", "/config"]

  # Validate API endpoints
  endpoint_validation = [
    for idx, endpoint in var.api_endpoints : {
      index = idx
      path = endpoint.path
      method = endpoint.method

      # Path validation
      path_starts_with_slash = provider::pyvider::contains(endpoint.path, "/") && substr(endpoint.path, 0, 1) == "/"
      path_length_valid = provider::pyvider::length(endpoint.path) > 1

      # Method validation
      method_valid = provider::pyvider::contains(local.valid_http_methods, endpoint.method)

      # Security validation
      is_admin_path = anytrue([
        for admin_path in local.admin_paths :
        provider::pyvider::contains(endpoint.path, admin_path)
      ])
      admin_path_secure = local.is_admin_path ? endpoint.auth : true

      # Auth/public consistency
      auth_public_conflict = endpoint.auth && provider::pyvider::lookup(endpoint, "public", false)

      # Overall validation
      is_valid = (
        local.path_starts_with_slash &&
        local.path_length_valid &&
        local.method_valid &&
        local.admin_path_secure &&
        !local.auth_public_conflict
      )

      # Collect errors
      errors = concat(
        !local.path_starts_with_slash ? ["Path must start with /"] : [],
        !local.path_length_valid ? ["Path must be longer than 1 character"] : [],
        !local.method_valid ? ["Invalid HTTP method: ${endpoint.method}"] : [],
        !local.admin_path_secure ? ["Admin paths must require authentication"] : [],
        local.auth_public_conflict ? ["Cannot be both authenticated and public"] : []
      )
    }
  ]

  # API endpoint summary
  total_endpoints = provider::pyvider::length(var.api_endpoints)
  valid_endpoints = [for result in local.endpoint_validation : result if result.is_valid]
  invalid_endpoints = [for result in local.endpoint_validation : result if !result.is_valid]
  valid_endpoint_count = provider::pyvider::length(local.valid_endpoints)
  invalid_endpoint_count = provider::pyvider::length(local.invalid_endpoints)
}

# Create validation reports
resource "pyvider_file_content" "user_validation_report" {
  filename = "/tmp/user_validation_report.txt"
  content = join("\n", concat(
    [
      "=== User Registration Validation Report ===",
      "",
      "Summary:",
      "  Total users: ${local.total_users}",
      "  Valid users: ${local.valid_count}",
      "  Invalid users: ${local.invalid_count}",
      "",
      "Validation Rules:",
      "  - Required fields: ${join(", ", local.required_fields)}",
      "  - Username length: ${local.min_username_length}-${local.max_username_length} characters",
      "  - Username cannot contain @ symbol",
      "  - Email must contain @ and . symbols",
      "  - Valid roles: ${join(", ", local.valid_roles)}",
      "",
      "Results:"
    ],
    flatten([
      for result in local.validation_results : [
        "",
        "User ${result.index + 1}: ${result.username}",
        "  Email: ${result.email}",
        "  Status: ${result.is_valid ? "VALID" : "INVALID"}",
        result.is_valid ? "" : "  Errors: ${join(", ", result.errors)}"
      ]
    ])
  ))
}

resource "pyvider_file_content" "service_validation_report" {
  filename = "/tmp/service_validation_report.txt"
  content = join("\n", concat(
    [
      "=== Service Configuration Validation Report ===",
      "",
      "Summary:",
      "  Total services: ${local.total_services}",
      "  Valid services: ${local.valid_service_count}",
      "  Invalid services: ${local.invalid_service_count}",
      "",
      "Validation Rules:",
      "  - Required fields: ${join(", ", local.required_service_fields)}",
      "  - Valid protocols: ${join(", ", local.valid_protocols)}",
      "  - SSL consistency with protocol",
      "  - Port range: 1-65535",
      "",
      "Results:"
    ],
    flatten([
      for service_name, validation in local.service_validation : [
        "",
        "Service: ${service_name}",
        "  Status: ${validation.is_valid ? "VALID" : "INVALID"}",
        validation.is_valid ? "" : "  Errors: ${join(", ", validation.errors)}"
      ]
    ])
  ))
}

resource "pyvider_file_content" "api_validation_report" {
  filename = "/tmp/api_validation_report.txt"
  content = join("\n", concat(
    [
      "=== API Endpoint Validation Report ===",
      "",
      "Summary:",
      "  Total endpoints: ${local.total_endpoints}",
      "  Valid endpoints: ${local.valid_endpoint_count}",
      "  Invalid endpoints: ${local.invalid_endpoint_count}",
      "",
      "Validation Rules:",
      "  - Path must start with /",
      "  - Valid HTTP methods: ${join(", ", local.valid_http_methods)}",
      "  - Admin paths must require authentication",
      "  - Cannot be both authenticated and public",
      "",
      "Results:"
    ],
    flatten([
      for result in local.endpoint_validation : [
        "",
        "Endpoint ${result.index + 1}: ${result.method} ${result.path}",
        "  Status: ${result.is_valid ? "VALID" : "INVALID"}",
        result.is_valid ? "" : "  Errors: ${join(", ", result.errors)}"
      ]
    ])
  ))
}

# Output validation results
output "data_validation_results" {
  value = {
    user_validation = {
      total = local.total_users
      valid = local.valid_count
      invalid = local.invalid_count
      report_file = pyvider_file_content.user_validation_report.filename
    }

    service_validation = {
      total = local.total_services
      valid = local.valid_service_count
      invalid = local.invalid_service_count
      valid_services = local.valid_services
      invalid_services = local.invalid_services
      report_file = pyvider_file_content.service_validation_report.filename
    }

    api_validation = {
      total = local.total_endpoints
      valid = local.valid_endpoint_count
      invalid = local.invalid_endpoint_count
      report_file = pyvider_file_content.api_validation_report.filename
    }

    summary = {
      all_users_valid = local.invalid_count == 0
      all_services_valid = local.invalid_service_count == 0
      all_endpoints_valid = local.invalid_endpoint_count == 0
      overall_valid = (
        local.invalid_count == 0 &&
        local.invalid_service_count == 0 &&
        local.invalid_endpoint_count == 0
      )
    }
  }
}