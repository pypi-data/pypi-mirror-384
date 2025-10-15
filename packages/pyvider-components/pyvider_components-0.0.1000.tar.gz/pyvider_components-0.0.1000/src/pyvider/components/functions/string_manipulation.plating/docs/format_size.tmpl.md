---
page_title: "Function: format_size"
description: |-
  Formats byte values as human-readable file sizes with customizable precision
---

# format_size (Function)

> Converts byte values to human-readable file size strings with automatic unit selection

The `format_size` function formats byte values into human-readable strings using appropriate units (B, KB, MB, GB, TB, PB). It automatically selects the most appropriate unit and allows customizable decimal precision.

## When to Use This

- **File size display**: Show file sizes in user-friendly format
- **Storage reports**: Display storage usage and capacity
- **Bandwidth monitoring**: Format network transfer amounts
- **Memory usage**: Display RAM or cache sizes
- **Progress indicators**: Show download/upload progress

**Anti-patterns (when NOT to use):**
- When exact byte values are needed for calculations
- For non-size numeric values (use appropriate number formatting)
- When binary units (1024-based) are specifically required
- In APIs where raw byte values are expected

## Quick Start

```terraform
# Format file sizes
locals {
  file_sizes = [1024, 1048576, 1073741824]
  formatted_sizes = [
    for size in local.file_sizes :
    provider::pyvider::format_size(size)
  ]
  # Returns: ["1.0 KB", "1.0 MB", "1.0 GB"]
}

# Custom precision
locals {
  large_file = 1234567890
  precise_size = provider::pyvider::format_size(local.large_file, 2)  # Returns: "1.15 GB"
  rounded_size = provider::pyvider::format_size(local.large_file, 0)  # Returns: "1 GB"
}
```

## Examples

### Basic Usage

```terraform
# Basic file size formatting
locals {
  byte_values = [0, 512, 1024, 1536, 1048576, 1073741824, 1099511627776]

  # Format with default precision (1 decimal place)
  formatted_default = [
    for size in local.byte_values :
    provider::pyvider::format_size(size)
  ]
  # Results: ["0 B", "512 B", "1.0 KB", "1.5 KB", "1.0 MB", "1.0 GB", "1.0 TB"]

  # Different precision levels
  test_size = 1234567890  # ~1.15 GB

  precision_examples = {
    no_decimals = provider::pyvider::format_size(local.test_size, 0)   # "1 GB"
    one_decimal = provider::pyvider::format_size(local.test_size, 1)   # "1.1 GB"
    two_decimals = provider::pyvider::format_size(local.test_size, 2)  # "1.15 GB"
    three_decimals = provider::pyvider::format_size(local.test_size, 3) # "1.149 GB"
  }
}

# Edge cases and special values
locals {
  edge_cases = {
    zero_bytes = provider::pyvider::format_size(0)          # "0 B"
    one_byte = provider::pyvider::format_size(1)            # "1 B"
    very_large = provider::pyvider::format_size(1152921504606846976)  # "1.0 EB"
    null_value = provider::pyvider::format_size(null)       # null
    negative = provider::pyvider::format_size(-1024)        # "-1.0 KB"
  }

  # Common size benchmarks
  size_benchmarks = {
    floppy_disk = provider::pyvider::format_size(1474560)     # "1.4 MB"
    cd_rom = provider::pyvider::format_size(737280000)        # "703.1 MB"
    dvd = provider::pyvider::format_size(4700000000)          # "4.4 GB"
    blu_ray = provider::pyvider::format_size(25000000000)     # "23.3 GB"
    typical_photo = provider::pyvider::format_size(3145728)   # "3.0 MB"
    typical_song = provider::pyvider::format_size(4194304)    # "4.0 MB"
    hd_movie = provider::pyvider::format_size(1073741824)     # "1.0 GB"
  }
}

output "basic_formatting" {
  value = {
    default_precision = local.formatted_default
    precision_levels = local.precision_examples
    edge_cases = local.edge_cases
    benchmarks = local.size_benchmarks
  }
}
```

### Storage Analysis

```terraform
# Cloud storage usage analysis
variable "storage_buckets" {
  type = list(object({
    name         = string
    region       = string
    usage_bytes  = number
    limit_bytes  = number
    cost_per_gb  = number
  }))
  default = [
    {
      name = "app-data-prod"
      region = "us-east-1"
      usage_bytes = 5368709120    # 5 GB
      limit_bytes = 21474836480   # 20 GB
      cost_per_gb = 0.023
    },
    {
      name = "backups-archive"
      region = "us-west-2"
      usage_bytes = 107374182400  # 100 GB
      limit_bytes = 1099511627776 # 1 TB
      cost_per_gb = 0.012
    }
  ]
}

# Generate storage reports
locals {
  storage_analysis = {
    for bucket in var.storage_buckets :
    bucket.name => {
      current_usage = provider::pyvider::format_size(bucket.usage_bytes, 1)
      storage_limit = provider::pyvider::format_size(bucket.limit_bytes, 0)
      available_space = provider::pyvider::format_size(bucket.limit_bytes - bucket.usage_bytes, 1)

      utilization_percent = round((bucket.usage_bytes / bucket.limit_bytes) * 100, 1)

      # Cost analysis
      usage_gb = bucket.usage_bytes / 1073741824  # Convert to GB
      monthly_cost = round(local.storage_analysis[bucket.name].usage_gb * bucket.cost_per_gb, 2)

      # Status and recommendations
      status = local.storage_analysis[bucket.name].utilization_percent > 80 ? "Critical" :
               local.storage_analysis[bucket.name].utilization_percent > 60 ? "Warning" : "OK"

      recommendation = local.storage_analysis[bucket.name].utilization_percent > 80 ?
        "Consider expanding storage or archiving old data" :
        local.storage_analysis[bucket.name].utilization_percent > 60 ?
        "Monitor usage closely" : "Usage within normal limits"

      # Human-readable summary
      summary = "Bucket '${bucket.name}' in ${bucket.region}: ${local.storage_analysis[bucket.name].current_usage} used of ${local.storage_analysis[bucket.name].storage_limit} (${local.storage_analysis[bucket.name].utilization_percent}% full)"
    }
  }

  # Aggregate statistics
  total_usage_bytes = sum([for bucket in var.storage_buckets : bucket.usage_bytes])
  total_limit_bytes = sum([for bucket in var.storage_buckets : bucket.limit_bytes])

  aggregate_stats = {
    total_used = provider::pyvider::format_size(local.total_usage_bytes, 1)
    total_capacity = provider::pyvider::format_size(local.total_limit_bytes, 0)
    total_available = provider::pyvider::format_size(local.total_limit_bytes - local.total_usage_bytes, 1)
    overall_utilization = "${round((local.total_usage_bytes / local.total_limit_bytes) * 100, 1)}%"
  }
}

# Database storage monitoring
variable "database_metrics" {
  type = object({
    data_size_bytes  = number
    index_size_bytes = number
    log_size_bytes   = number
    temp_size_bytes  = number
    backup_size_bytes = number
  })
  default = {
    data_size_bytes = 12884901888    # 12 GB
    index_size_bytes = 2147483648    # 2 GB
    log_size_bytes = 536870912       # 512 MB
    temp_size_bytes = 268435456      # 256 MB
    backup_size_bytes = 25769803776  # 24 GB
  }
}

locals {
  database_analysis = {
    data_size = provider::pyvider::format_size(var.database_metrics.data_size_bytes, 1)
    index_size = provider::pyvider::format_size(var.database_metrics.index_size_bytes, 1)
    log_size = provider::pyvider::format_size(var.database_metrics.log_size_bytes, 0)
    temp_size = provider::pyvider::format_size(var.database_metrics.temp_size_bytes, 0)
    backup_size = provider::pyvider::format_size(var.database_metrics.backup_size_bytes, 1)

    total_size = provider::pyvider::format_size(
      var.database_metrics.data_size_bytes +
      var.database_metrics.index_size_bytes +
      var.database_metrics.log_size_bytes +
      var.database_metrics.temp_size_bytes, 1
    )

    # Storage breakdown percentages
    total_bytes = var.database_metrics.data_size_bytes + var.database_metrics.index_size_bytes +
                  var.database_metrics.log_size_bytes + var.database_metrics.temp_size_bytes

    data_percentage = round((var.database_metrics.data_size_bytes / local.database_analysis.total_bytes) * 100, 1)
    index_percentage = round((var.database_metrics.index_size_bytes / local.database_analysis.total_bytes) * 100, 1)

    storage_breakdown = "Data: ${local.database_analysis.data_size} (${local.database_analysis.data_percentage}%), Indexes: ${local.database_analysis.index_size} (${local.database_analysis.index_percentage}%), Logs: ${local.database_analysis.log_size}, Temp: ${local.database_analysis.temp_size}"
  }
}

output "storage_analysis" {
  value = {
    bucket_details = local.storage_analysis
    aggregate_stats = local.aggregate_stats
    database_metrics = local.database_analysis
  }
}
```

### File Management

```terraform
# File upload and management system
variable "file_uploads" {
  type = list(object({
    filename = string
    size_bytes = number
    mime_type = string
    upload_date = string
    user_id = string
  }))
  default = [
    {
      filename = "presentation.pptx"
      size_bytes = 15728640  # 15 MB
      mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      upload_date = "2024-01-15"
      user_id = "user-123"
    },
    {
      filename = "dataset.csv"
      size_bytes = 104857600  # 100 MB
      mime_type = "text/csv"
      upload_date = "2024-01-16"
      user_id = "user-456"
    },
    {
      filename = "backup.zip"
      size_bytes = 536870912  # 512 MB
      mime_type = "application/zip"
      upload_date = "2024-01-17"
      user_id = "user-789"
    }
  ]
}

# File processing and display
locals {
  file_management = {
    for file in var.file_uploads :
    file.filename => {
      # Human-readable size
      display_size = provider::pyvider::format_size(file.size_bytes, 1)

      # File type categorization
      category = can(regex("^image/", file.mime_type)) ? "image" :
                can(regex("^video/", file.mime_type)) ? "video" :
                can(regex("^audio/", file.mime_type)) ? "audio" :
                can(regex("^text/", file.mime_type)) ? "document" :
                can(regex("application/(pdf|msword|vnd\\.)", file.mime_type)) ? "document" :
                can(regex("application/(zip|rar|tar|gzip)", file.mime_type)) ? "archive" : "other"

      # Size-based recommendations
      size_category = file.size_bytes < 1048576 ? "small" :          # < 1 MB
                     file.size_bytes < 104857600 ? "medium" :        # < 100 MB
                     file.size_bytes < 1073741824 ? "large" : "huge" # < 1 GB

      # Upload validation
      max_size = local.file_management[file.filename].category == "image" ? 10485760 :     # 10 MB
                local.file_management[file.filename].category == "document" ? 52428800 :   # 50 MB
                local.file_management[file.filename].category == "video" ? 2147483648 :    # 2 GB
                local.file_management[file.filename].category == "archive" ? 1073741824 :  # 1 GB
                104857600  # Default 100 MB

      size_valid = file.size_bytes <= local.file_management[file.filename].max_size
      max_size_display = provider::pyvider::format_size(local.file_management[file.filename].max_size, 0)

      # File listing display
      file_summary = "${file.filename} (${local.file_management[file.filename].display_size}) - ${local.file_management[file.filename].category}"

      # Storage efficiency
      compression_ratio = local.file_management[file.filename].category == "archive" ?
        "${round((file.size_bytes / (file.size_bytes * 0.7)) * 100, 0)}% of original" : "N/A"
    }
  }

  # User quota management
  user_quotas = {
    for user_id in distinct([for file in var.file_uploads : file.user_id]) :
    user_id => {
      files = [for file in var.file_uploads : file if file.user_id == user_id]

      total_bytes = sum([for file in local.user_quotas[user_id].files : file.size_bytes])
      file_count = length(local.user_quotas[user_id].files)

      total_size = provider::pyvider::format_size(local.user_quotas[user_id].total_bytes, 1)
      quota_limit = 2147483648  # 2 GB per user
      quota_limit_display = provider::pyvider::format_size(local.user_quotas[user_id].quota_limit, 0)
      remaining_quota = provider::pyvider::format_size(local.user_quotas[user_id].quota_limit - local.user_quotas[user_id].total_bytes, 1)

      quota_usage_percent = round((local.user_quotas[user_id].total_bytes / local.user_quotas[user_id].quota_limit) * 100, 1)

      status = local.user_quotas[user_id].quota_usage_percent > 90 ? "Over limit" :
               local.user_quotas[user_id].quota_usage_percent > 75 ? "Near limit" : "OK"

      summary = "User ${user_id}: ${local.user_quotas[user_id].file_count} files using ${local.user_quotas[user_id].total_size} of ${local.user_quotas[user_id].quota_limit_display} quota (${local.user_quotas[user_id].quota_usage_percent}%)"
    }
  }

  # System-wide file statistics
  system_stats = {
    total_files = length(var.file_uploads)
    total_storage = provider::pyvider::format_size(sum([for file in var.file_uploads : file.size_bytes]), 1)
    average_file_size = provider::pyvider::format_size(
      sum([for file in var.file_uploads : file.size_bytes]) / length(var.file_uploads), 1
    )

    largest_file = {
      for file in var.file_uploads :
      file.filename => provider::pyvider::format_size(file.size_bytes, 1)
      if file.size_bytes == max([for f in var.file_uploads : f.size_bytes]...)
    }
  }
}

output "file_management" {
  value = {
    file_details = local.file_management
    user_quotas = local.user_quotas
    system_statistics = local.system_stats
  }
}
```

## Signature

`format_size(size_bytes: number, precision?: number) -> string`

## Arguments

- **`size_bytes`** (number, required) - The size in bytes to format. Can be any numeric value including:
  - Positive integers: Standard file sizes
  - Zero: Returns "0 B"
  - Negative numbers: Formatted with negative sign
  - Decimals: Rounded to specified precision
  - If `null`, returns `null`
- **`precision`** (number, optional) - Number of decimal places to display. Defaults to `1`.
  - `0`: No decimal places → "1 GB"
  - `1`: One decimal place → "1.2 GB"
  - `2` or higher: Multiple decimal places → "1.23 GB"

## Return Value

Returns a formatted string with size and appropriate unit:
- **Units used**: B, KB, MB, GB, TB, PB, EB (1000-based, decimal)
- **Format**: `"<number> <unit>"` (e.g., "1.5 MB")
- **Automatic unit selection**: Chooses the largest appropriate unit
- **Precision**: Respects the specified decimal places
- **Null handling**: Returns `null` when input is `null`

## Unit Conversion

The function uses decimal (1000-based) units:
- **1 KB** = 1,000 bytes
- **1 MB** = 1,000,000 bytes
- **1 GB** = 1,000,000,000 bytes
- **1 TB** = 1,000,000,000,000 bytes
- **1 PB** = 1,000,000,000,000,000 bytes
- **1 EB** = 1,000,000,000,000,000,000 bytes

Note: This follows SI (International System of Units) standards, not binary (1024-based) units.

## Common Use Cases

```terraform
# File system reporting
locals {
  disk_usage = provider::pyvider::format_size(524288000, 1)    # "524.3 MB"

  # User interface display
  file_size = provider::pyvider::format_size(1048576, 0)      # "1 MB"

  # API responses
  download_size = provider::pyvider::format_size(2097152, 2)  # "2.10 MB"

  # Storage capacity planning
  total_capacity = provider::pyvider::format_size(2199023255552, 0)  # "2 TB"
}
```

## Related Functions

- [`tostring`](./tostring.md) - Convert values to string format
- [`round`](./round.md) - Round numeric values
- [`add`](./add.md) - Add numeric values for totals
- [`multiply`](./multiply.md) - Calculate size multiplications
- [`divide`](./divide.md) - Calculate size divisions