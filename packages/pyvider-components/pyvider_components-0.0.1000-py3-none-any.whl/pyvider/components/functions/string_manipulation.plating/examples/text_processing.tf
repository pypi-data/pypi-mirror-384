# Text processing examples using string manipulation functions

# Configuration file processing
variable "config_template" {
  type    = string
  default = "server_name: {hostname}\nport: {port}\ndebug: {debug_mode}\nlog_level: {level}"
}

variable "server_config" {
  type = object({
    hostname   = string
    port       = number
    debug_mode = bool
    level      = string
  })
  default = {
    hostname   = "web-server-01"
    port       = 8080
    debug_mode = true
    level      = "INFO"
  }
}

locals {
  # Generate configuration content
  config_content = provider::pyvider::format(var.config_template, {
    hostname   = var.server_config.hostname
    port       = var.server_config.port
    debug_mode = var.server_config.debug_mode
    level      = provider::pyvider::upper(var.server_config.level)
  })

  # Create normalized filename from hostname
  config_filename = provider::pyvider::format("{name}_config.yaml", {
    name = provider::pyvider::lower(
      provider::pyvider::replace(var.server_config.hostname, "-", "_")
    )
  })
}

# Log file path generation
variable "log_entries" {
  type = list(string)
  default = [
    "2024-01-15 10:30:15 INFO Application started",
    "2024-01-15 10:30:16 DEBUG Database connection established",
    "2024-01-15 10:30:17 WARN Cache miss for key: user_123",
    "2024-01-15 10:30:18 ERROR Failed to process request"
  ]
}

locals {
  # Parse log levels from entries
  log_levels = [
    for entry in var.log_entries :
    provider::pyvider::split(entry, " ")[2]  # Extract the log level (3rd element)
  ]

  # Create log summary
  log_summary = provider::pyvider::join([
    "Log Analysis Summary:",
    provider::pyvider::format("Total entries: {count}", {
      count = length(var.log_entries)
    }),
    provider::pyvider::format("Levels found: {levels}", {
      levels = provider::pyvider::join(local.log_levels, ", ")
    })
  ], "\n")
}

# URL and path manipulation
variable "base_urls" {
  type = list(string)
  default = [
    "https://api.example.com/v1/users",
    "https://api.example.com/v1/orders",
    "https://api.example.com/v1/products"
  ]
}

variable "api_endpoints" {
  type = list(string)
  default = ["list", "create", "update", "delete"]
}

locals {
  # Generate all possible API endpoint URLs
  api_urls = flatten([
    for base_url in var.base_urls : [
      for endpoint in var.api_endpoints :
      provider::pyvider::format("{base}/{action}", {
        base   = base_url
        action = endpoint
      })
    ]
  ])

  # Extract service names from URLs
  service_names = [
    for url in var.base_urls :
    provider::pyvider::split(provider::pyvider::split(url, "/")[4], "?")[0]  # Extract path segment after v1
  ]
}

# Environment variable processing
variable "env_config" {
  type = map(string)
  default = {
    APP_NAME     = "MyApplication"
    APP_VERSION  = "1.2.3"
    DEBUG_MODE   = "true"
    DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb"
  }
}

locals {
  # Convert environment variables to different formats
  env_exports = [
    for key, value in var.env_config :
    provider::pyvider::format("export {key}={value}", {
      key   = key
      value = provider::pyvider::format("\"{val}\"", { val = value })
    })
  ]

  # Create .env file content
  env_file_content = provider::pyvider::join(local.env_exports, "\n")

  # Generate application title from app name
  app_title = provider::pyvider::replace(
    provider::pyvider::upper(var.env_config.APP_NAME),
    "_",
    " "
  )
}

# CSV data processing
variable "csv_data" {
  type    = string
  default = "name,age,city\nAlice,30,New York\nBob,25,Los Angeles\nCharlie,35,Chicago"
}

locals {
  # Split CSV into rows
  csv_rows = provider::pyvider::split(var.csv_data, "\n")

  # Extract header and data rows
  csv_header = provider::pyvider::split(local.csv_rows[0], ",")
  csv_data_rows = slice(local.csv_rows, 1, length(local.csv_rows))

  # Process each data row
  csv_records = [
    for row in local.csv_data_rows : {
      name = provider::pyvider::split(row, ",")[0]
      age  = provider::pyvider::split(row, ",")[1]
      city = provider::pyvider::split(row, ",")[2]
    }
  ]

  # Generate a summary report
  csv_summary = provider::pyvider::join([
    "CSV Processing Summary:",
    provider::pyvider::format("Columns: {headers}", {
      headers = provider::pyvider::join(local.csv_header, ", ")
    }),
    provider::pyvider::format("Records: {count}", {
      count = length(local.csv_records)
    }),
    "Sample record:",
    provider::pyvider::format("  {name} ({age}) from {city}", {
      name = local.csv_records[0].name
      age  = local.csv_records[0].age
      city = local.csv_records[0].city
    })
  ], "\n")
}

# Create output files with processed content
resource "pyvider_file_content" "server_config" {
  filename = "/tmp/${local.config_filename}"
  content  = local.config_content
}

resource "pyvider_file_content" "log_analysis" {
  filename = "/tmp/log_analysis.txt"
  content  = local.log_summary
}

resource "pyvider_file_content" "api_urls" {
  filename = "/tmp/api_endpoints.txt"
  content = join("\n", concat(
    ["Generated API Endpoints:", ""],
    local.api_urls,
    ["", "Service Names:"],
    [for name in local.service_names : "- ${name}"]
  ))
}

resource "pyvider_file_content" "environment" {
  filename = "/tmp/app.env"
  content  = local.env_file_content
}

resource "pyvider_file_content" "csv_report" {
  filename = "/tmp/csv_processing_report.txt"
  content  = local.csv_summary
}

# Output processed data
output "text_processing_results" {
  value = {
    configuration = {
      filename = local.config_filename
      content_preview = substr(local.config_content, 0, 50)
      file_path = pyvider_file_content.server_config.filename
    }

    logging = {
      levels_found = local.log_levels
      summary_file = pyvider_file_content.log_analysis.filename
    }

    api_management = {
      total_urls = length(local.api_urls)
      service_count = length(local.service_names)
      services = local.service_names
      urls_file = pyvider_file_content.api_urls.filename
    }

    environment = {
      app_title = local.app_title
      env_file = pyvider_file_content.environment.filename
      export_count = length(local.env_exports)
    }

    csv_processing = {
      header_columns = local.csv_header
      record_count = length(local.csv_records)
      sample_record = local.csv_records[0]
      report_file = pyvider_file_content.csv_report.filename
    }
  }
}