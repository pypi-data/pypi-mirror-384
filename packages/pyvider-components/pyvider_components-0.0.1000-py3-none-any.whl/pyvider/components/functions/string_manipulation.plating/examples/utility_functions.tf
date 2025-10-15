# Utility function examples for format_size, truncate, and pluralize

# File size formatting examples
variable "storage_data" {
  type = list(object({
    name = string
    size_bytes = number
    type = string
  }))
  default = [
    { name = "system.log", size_bytes = 1024, type = "log" },
    { name = "database.db", size_bytes = 2147483648, type = "database" },
    { name = "backup.tar.gz", size_bytes = 5368709120, type = "archive" },
    { name = "cache.tmp", size_bytes = 134217728, type = "cache" },
    { name = "config.json", size_bytes = 2048, type = "config" },
    { name = "media.mp4", size_bytes = 1073741824, type = "media" }
  ]
}

locals {
  # Format file sizes with different precisions
  file_size_analysis = [
    for file in var.storage_data : {
      name = file.name
      type = file.type
      raw_bytes = file.size_bytes
      size_default = provider::pyvider::format_size(file.size_bytes)      # 1 decimal place (default)
      size_precise = provider::pyvider::format_size(file.size_bytes, 2)  # 2 decimal places
      size_rounded = provider::pyvider::format_size(file.size_bytes, 0)  # No decimal places
    }
  ]

  # Calculate totals by file type
  totals_by_type = {
    for type in distinct([for f in var.storage_data : f.type]) :
    type => sum([for f in var.storage_data : f.size_bytes if f.type == type])
  }

  formatted_totals = {
    for type, total_bytes in local.totals_by_type :
    type => {
      bytes = total_bytes
      formatted = provider::pyvider::format_size(total_bytes, 1)
      file_count = length([for f in var.storage_data : f if f.type == type])
    }
  }
}

# Text truncation examples
variable "content_samples" {
  type = list(object({
    title = string
    description = string
    category = string
  }))
  default = [
    {
      title = "Getting Started with Infrastructure as Code using Terraform"
      description = "This comprehensive guide covers everything you need to know about Infrastructure as Code (IaC) principles and practices. Learn how to manage your infrastructure using declarative configuration files, version control best practices, and automated deployment strategies that will improve your development workflow."
      category = "Tutorial"
    },
    {
      title = "Advanced Terraform Provider Development Techniques"
      description = "Dive deep into custom Terraform provider development with advanced patterns, testing strategies, and performance optimization techniques for enterprise-scale infrastructure management."
      category = "Advanced"
    },
    {
      title = "Quick Reference"
      description = "Commands and syntax."
      category = "Reference"
    }
  ]
}

locals {
  # Create different truncation examples
  content_previews = [
    for content in var.content_samples : {
      original_title = content.title
      original_description = content.description
      category = content.category

      # Title truncations for different contexts
      short_title = provider::pyvider::truncate(content.title, 30, "...")
      medium_title = provider::pyvider::truncate(content.title, 50, "...")
      card_title = provider::pyvider::truncate(content.title, 40, " [more]")

      # Description truncations
      preview_short = provider::pyvider::truncate(content.description, 100, "... [Read more]")
      preview_medium = provider::pyvider::truncate(content.description, 200, "...")
      tweet_length = provider::pyvider::truncate(content.description, 140, "... #terraform")

      # No truncation needed examples
      title_fits = provider::pyvider::length(content.title) <= 50
      description_fits = provider::pyvider::length(content.description) <= 200
    }
  ]
}

# Pluralization examples
variable "system_stats" {
  type = object({
    users = number
    active_sessions = number
    files = number
    errors = number
    warnings = number
    processes = number
    memory_mb = number
    disk_gb = number
  })
  default = {
    users = 1
    active_sessions = 23
    files = 1456
    errors = 0
    warnings = 5
    processes = 47
    memory_mb = 8192
    disk_gb = 500
  }
}

locals {
  # Create user-friendly status messages
  system_status_messages = [
    {
      category = "Users"
      message = var.system_stats.users == 0 ?
        "No users online" :
        "${var.system_stats.users} ${provider::pyvider::pluralize("user", var.system_stats.users)} online"
    },
    {
      category = "Sessions"
      message = "${var.system_stats.active_sessions} active ${provider::pyvider::pluralize("session", var.system_stats.active_sessions)}"
    },
    {
      category = "Files"
      message = "${var.system_stats.files} ${provider::pyvider::pluralize("file", var.system_stats.files)} in system"
    },
    {
      category = "Issues"
      message = var.system_stats.errors == 0 && var.system_stats.warnings == 0 ?
        "No issues detected" :
        join(" and ", compact([
          var.system_stats.errors > 0 ? "${var.system_stats.errors} ${provider::pyvider::pluralize("error", var.system_stats.errors)}" : "",
          var.system_stats.warnings > 0 ? "${var.system_stats.warnings} ${provider::pyvider::pluralize("warning", var.system_stats.warnings)}" : ""
        ]))
    },
    {
      category = "Processes"
      message = "${var.system_stats.processes} ${provider::pyvider::pluralize("process", var.system_stats.processes)} running"
    }
  ]
}

# Irregular plurals examples
variable "inventory_counts" {
  type = map(number)
  default = {
    "child" = 3
    "person" = 12
    "mouse" = 1
    "foot" = 2
    "tooth" = 28
    "goose" = 0
    "ox" = 4
    "woman" = 7
    "man" = 15
  }
}

locals {
  # Handle irregular plurals with custom forms
  irregular_plurals = {
    "child" = "children"
    "person" = "people"
    "mouse" = "mice"
    "foot" = "feet"
    "tooth" = "teeth"
    "goose" = "geese"
    "ox" = "oxen"
    "woman" = "women"
    "man" = "men"
  }

  inventory_messages = [
    for word, count in var.inventory_counts : {
      word = word
      count = count
      message = "${count} ${provider::pyvider::pluralize(word, count, lookup(local.irregular_plurals, word, null))}"
    }
  ]
}

# Combined utility function examples
variable "log_entries" {
  type = list(object({
    timestamp = string
    level = string
    message = string
    component = string
    size_bytes = number
  }))
  default = [
    {
      timestamp = "2024-01-15T10:30:15Z"
      level = "ERROR"
      message = "Database connection failed after multiple retry attempts. Connection timeout exceeded while trying to establish connection to primary database server."
      component = "DatabaseService"
      size_bytes = 256
    },
    {
      timestamp = "2024-01-15T10:30:16Z"
      level = "INFO"
      message = "Successfully processed user authentication request"
      component = "AuthService"
      size_bytes = 128
    },
    {
      timestamp = "2024-01-15T10:30:17Z"
      level = "WARN"
      message = "Cache miss rate is higher than expected threshold"
      component = "CacheService"
      size_bytes = 164
    }
  ]
}

locals {
  # Process log entries with multiple utility functions
  processed_logs = [
    for idx, entry in var.log_entries : {
      index = idx + 1
      timestamp = entry.timestamp
      level = entry.level
      component = provider::pyvider::truncate(entry.component, 12, "")
      short_message = provider::pyvider::truncate(entry.message, 50, "...")
      full_message = entry.message
      entry_size = provider::pyvider::format_size(entry.size_bytes, 0)
      line_number = idx + 1
    }
  ]

  # Create log summary statistics
  log_stats = {
    total_entries = length(var.log_entries)
    total_size = sum([for entry in var.log_entries : entry.size_bytes])
    by_level = {
      for level in distinct([for entry in var.log_entries : entry.level]) :
      level => length([for entry in var.log_entries : entry if entry.level == level])
    }
  }

  log_summary_messages = [
    for level, count in local.log_stats.by_level :
    "${count} ${provider::pyvider::pluralize("entry", count)} at ${level} level"
  ]
}

# Performance metrics with utility functions
variable "performance_data" {
  type = object({
    response_times_ms = list(number)
    memory_usage_bytes = list(number)
    request_counts = list(number)
    error_counts = list(number)
  })
  default = {
    response_times_ms = [45, 123, 67, 234, 89, 156, 78, 201, 92, 134]
    memory_usage_bytes = [134217728, 268435456, 402653184, 536870912, 671088640]
    request_counts = [1250, 2340, 1876, 3456, 2109]
    error_counts = [0, 2, 1, 5, 0]
  }
}

locals {
  # Calculate performance statistics
  perf_stats = {
    response_time = {
      count = length(var.performance_data.response_times_ms)
      avg_ms = sum(var.performance_data.response_times_ms) / length(var.performance_data.response_times_ms)
      max_ms = max(var.performance_data.response_times_ms)
      min_ms = min(var.performance_data.response_times_ms)
    }
    memory = {
      samples = length(var.performance_data.memory_usage_bytes)
      avg_bytes = sum(var.performance_data.memory_usage_bytes) / length(var.performance_data.memory_usage_bytes)
      max_bytes = max(var.performance_data.memory_usage_bytes)
      peak_formatted = provider::pyvider::format_size(max(var.performance_data.memory_usage_bytes), 1)
      avg_formatted = provider::pyvider::format_size(sum(var.performance_data.memory_usage_bytes) / length(var.performance_data.memory_usage_bytes), 1)
    }
    requests = {
      total = sum(var.performance_data.request_counts)
      periods = length(var.performance_data.request_counts)
      avg_per_period = sum(var.performance_data.request_counts) / length(var.performance_data.request_counts)
    }
    errors = {
      total = sum(var.performance_data.error_counts)
      periods_with_errors = length([for count in var.performance_data.error_counts : count if count > 0])
    }
  }

  # Create human-readable performance summary
  performance_messages = [
    "Response Time: avg ${format("%.1f", local.perf_stats.response_time.avg_ms)}ms over ${local.perf_stats.response_time.count} ${provider::pyvider::pluralize("sample", local.perf_stats.response_time.count)}",
    "Memory Usage: peak ${local.perf_stats.memory.peak_formatted}, average ${local.perf_stats.memory.avg_formatted}",
    "Requests: ${local.perf_stats.requests.total} total across ${local.perf_stats.requests.periods} ${provider::pyvider::pluralize("period", local.perf_stats.requests.periods)}",
    "Errors: ${local.perf_stats.errors.total} ${provider::pyvider::pluralize("error", local.perf_stats.errors.total)} in ${local.perf_stats.errors.periods_with_errors} ${provider::pyvider::pluralize("period", local.perf_stats.errors.periods_with_errors)}"
  ]
}

# Create comprehensive output files
resource "pyvider_file_content" "storage_analysis" {
  filename = "/tmp/storage_analysis.txt"
  content = join("\n", concat(
    ["=== Storage Analysis Report ===", ""],
    ["Individual Files:"],
    [
      for file in local.file_size_analysis :
      "${file.name} (${file.type}): ${file.size_precise} (${file.raw_bytes} bytes)"
    ],
    ["", "Totals by Type:"],
    [
      for type, info in local.formatted_totals :
      "${type}: ${info.formatted} across ${info.file_count} ${provider::pyvider::pluralize("file", info.file_count)}"
    ]
  ))
}

resource "pyvider_file_content" "content_previews" {
  filename = "/tmp/content_previews.html"
  content = join("\n", flatten([
    ["<!DOCTYPE html>", "<html>", "<head><title>Content Previews</title></head>", "<body>", "<h1>Content Preview Examples</h1>"],
    [
      for preview in local.content_previews : [
        "<div class=\"content-item\">",
        "  <h3>${preview.short_title}</h3>",
        "  <p class=\"preview\">${preview.preview_short}</p>",
        "  <small>Category: ${preview.category}</small>",
        "  <p><strong>Original:</strong> ${preview.original_title}</p>",
        "</div>",
        ""
      ]
    ],
    ["</body>", "</html>"]
  ]))
}

resource "pyvider_file_content" "system_status" {
  filename = "/tmp/system_status.txt"
  content = join("\n", concat(
    ["=== System Status Dashboard ===", ""],
    [for status in local.system_status_messages : "${status.category}: ${status.message}"],
    ["", "=== Memory & Storage ==="],
    ["Memory: ${provider::pyvider::format_size(var.system_stats.memory_mb * 1024 * 1024, 1)}"],
    ["Disk: ${provider::pyvider::format_size(var.system_stats.disk_gb * 1024 * 1024 * 1024, 1)}"]
  ))
}

resource "pyvider_file_content" "log_summary" {
  filename = "/tmp/log_summary.txt"
  content = join("\n", concat(
    ["=== Log Analysis Summary ===", ""],
    ["Processed ${local.log_stats.total_entries} ${provider::pyvider::pluralize("entry", local.log_stats.total_entries)} (${provider::pyvider::format_size(local.log_stats.total_size, 1)})"],
    [""],
    ["By Level:"],
    local.log_summary_messages,
    ["", "Recent Entries:"],
    [
      for log in local.processed_logs :
      "[${log.timestamp}] ${log.level} ${log.component}: ${log.short_message} (${log.entry_size})"
    ]
  ))
}

resource "pyvider_file_content" "performance_report" {
  filename = "/tmp/performance_report.txt"
  content = join("\n", concat(
    ["=== Performance Analysis Report ===", ""],
    local.performance_messages
  ))
}

resource "pyvider_file_content" "pluralization_examples" {
  filename = "/tmp/pluralization_examples.txt"
  content = join("\n", concat(
    ["=== Pluralization Examples ===", ""],
    ["Regular Plurals:"],
    [for status in local.system_status_messages : "- ${status.message}"],
    ["", "Irregular Plurals:"],
    [for item in local.inventory_messages : "- ${item.message}"]
  ))
}

# Output comprehensive results
output "utility_function_results" {
  value = {
    file_storage = {
      files_analyzed = length(local.file_size_analysis)
      types_found = length(local.formatted_totals)
      total_storage = provider::pyvider::format_size(sum(values(local.totals_by_type)), 2)
      report_file = pyvider_file_content.storage_analysis.filename
    }

    content_management = {
      content_items = length(local.content_previews)
      preview_file = pyvider_file_content.content_previews.filename
      truncation_examples = length(local.content_previews) * 3  # 3 truncation types per item
    }

    system_monitoring = {
      status_messages = length(local.system_status_messages)
      status_file = pyvider_file_content.system_status.filename
      log_entries = length(local.processed_logs)
      log_file = pyvider_file_content.log_summary.filename
    }

    performance_analysis = {
      metrics_processed = 4  # response_time, memory, requests, errors
      report_file = pyvider_file_content.performance_report.filename
      summary_messages = length(local.performance_messages)
    }

    pluralization = {
      regular_examples = length(local.system_status_messages)
      irregular_examples = length(local.inventory_messages)
      examples_file = pyvider_file_content.pluralization_examples.filename
    }
  }
}