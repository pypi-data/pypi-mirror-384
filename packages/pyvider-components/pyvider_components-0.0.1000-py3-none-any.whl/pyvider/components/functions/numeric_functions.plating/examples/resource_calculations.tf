# Resource calculation examples using numeric functions

# Calculate total CPU cores across instances
variable "instance_types" {
  type = list(object({
    name  = string
    cores = number
    count = number
  }))
  default = [
    { name = "web", cores = 2, count = 3 },
    { name = "api", cores = 4, count = 2 },
    { name = "db", cores = 8, count = 1 }
  ]
}

locals {
  # Calculate cores per instance type
  web_total_cores = provider::pyvider::multiply(
    var.instance_types[0].cores,
    var.instance_types[0].count
  )  # 2 * 3 = 6

  api_total_cores = provider::pyvider::multiply(
    var.instance_types[1].cores,
    var.instance_types[1].count
  )  # 4 * 2 = 8

  db_total_cores = provider::pyvider::multiply(
    var.instance_types[2].cores,
    var.instance_types[2].count
  )  # 8 * 1 = 8

  # Sum all cores
  all_core_counts = [
    local.web_total_cores,
    local.api_total_cores,
    local.db_total_cores
  ]
  total_cores = provider::pyvider::sum(local.all_core_counts)  # 6 + 8 + 8 = 22
}

# Memory allocation calculations
variable "base_memory_gb" {
  type    = number
  default = 4
}

variable "memory_multiplier" {
  type    = number
  default = 1.5
}

locals {
  # Calculate memory per instance type
  web_memory_per_instance = provider::pyvider::multiply(
    var.base_memory_gb,
    var.memory_multiplier
  )  # 4 * 1.5 = 6

  # Round to nearest GB
  web_memory_rounded = provider::pyvider::round(local.web_memory_per_instance, 0)  # 6

  # Calculate total memory for web tier
  web_total_memory = provider::pyvider::multiply(
    local.web_memory_rounded,
    var.instance_types[0].count
  )  # 6 * 3 = 18
}

# Storage calculations
variable "base_storage_gb" {
  type    = number
  default = 100
}

variable "additional_storage_gb" {
  type    = number
  default = 50
}

locals {
  # Calculate storage per instance
  storage_per_instance = provider::pyvider::add(
    var.base_storage_gb,
    var.additional_storage_gb
  )  # 100 + 50 = 150

  # Calculate total storage needed
  total_instances = provider::pyvider::sum([
    var.instance_types[0].count,
    var.instance_types[1].count,
    var.instance_types[2].count
  ])  # 3 + 2 + 1 = 6

  total_storage = provider::pyvider::multiply(
    local.storage_per_instance,
    local.total_instances
  )  # 150 * 6 = 900
}

# Cost calculations
variable "cost_per_core_hour" {
  type    = number
  default = 0.05
}

variable "hours_per_month" {
  type    = number
  default = 730
}

locals {
  # Calculate monthly compute cost
  cost_per_core_month = provider::pyvider::multiply(
    var.cost_per_core_hour,
    var.hours_per_month
  )  # 0.05 * 730 = 36.5

  total_monthly_compute_cost = provider::pyvider::multiply(
    local.cost_per_core_month,
    local.total_cores
  )  # 36.5 * 22 = 803

  # Round to nearest dollar
  monthly_cost_rounded = provider::pyvider::round(local.total_monthly_compute_cost, 0)  # 803
}

# Create resource allocation summary
resource "pyvider_file_content" "resource_summary" {
  filename = "/tmp/resource_allocation.txt"
  content = join("\n", [
    "=== Resource Allocation Summary ===",
    "",
    "CPU Allocation:",
    "  Web tier: ${local.web_total_cores} cores (${var.instance_types[0].count} × ${var.instance_types[0].cores})",
    "  API tier: ${local.api_total_cores} cores (${var.instance_types[1].count} × ${var.instance_types[1].cores})",
    "  DB tier: ${local.db_total_cores} cores (${var.instance_types[2].count} × ${var.instance_types[2].cores})",
    "  Total: ${local.total_cores} cores",
    "",
    "Memory Allocation:",
    "  Web tier total: ${local.web_total_memory} GB",
    "  Per instance: ${local.web_memory_rounded} GB",
    "",
    "Storage Allocation:",
    "  Per instance: ${local.storage_per_instance} GB",
    "  Total instances: ${local.total_instances}",
    "  Total storage: ${local.total_storage} GB",
    "",
    "Cost Estimation:",
    "  Cost per core/month: $${local.cost_per_core_month}",
    "  Monthly compute cost: $${local.monthly_cost_rounded}",
    "",
    "Generated: ${timestamp()}"
  ])
}

# Output the calculations
output "resource_calculations" {
  value = {
    cpu = {
      web_cores = local.web_total_cores
      api_cores = local.api_total_cores
      db_cores = local.db_total_cores
      total_cores = local.total_cores
    }
    memory = {
      web_total_gb = local.web_total_memory
      per_instance_gb = local.web_memory_rounded
    }
    storage = {
      per_instance_gb = local.storage_per_instance
      total_instances = local.total_instances
      total_storage_gb = local.total_storage
    }
    cost = {
      monthly_compute = local.monthly_cost_rounded
      per_core_month = local.cost_per_core_month
    }
  }
}