# Complex JQ transformations for advanced data processing

# Example 1: Multi-level data processing
data "pyvider_lens_jq" "company_analysis" {
  json_input = jsonencode({
    company = "TechCorp"
    departments = [
      {
        name = "Engineering"
        budget = 2500000
        employees = [
          { name = "Alice", role = "Senior Engineer", salary = 120000, skills = ["Python", "Go", "Kubernetes"] },
          { name = "Bob", role = "Engineer", salary = 95000, skills = ["JavaScript", "React", "Node.js"] },
          { name = "Carol", role = "Tech Lead", salary = 140000, skills = ["Python", "AWS", "Docker"] }
        ]
      },
      {
        name = "Marketing"
        budget = 1200000
        employees = [
          { name = "Dave", role = "Marketing Manager", salary = 85000, skills = ["SEO", "Analytics", "Content"] },
          { name = "Eve", role = "Content Creator", salary = 65000, skills = ["Writing", "Design", "Social Media"] }
        ]
      },
      {
        name = "Sales"
        budget = 1800000
        employees = [
          { name = "Frank", role = "Sales Director", salary = 110000, skills = ["B2B Sales", "CRM", "Negotiation"] },
          { name = "Grace", role = "Account Manager", salary = 75000, skills = ["Customer Relations", "Salesforce"] }
        ]
      }
    ]
  })
  query = ".departments | map({
    department: .name,
    employee_count: (.employees | length),
    total_salary_cost: ([.employees[].salary] | add),
    avg_salary: (([.employees[].salary] | add) / (.employees | length)),
    budget_utilization: ((([.employees[].salary] | add) / .budget) * 100),
    skill_diversity: ([.employees[].skills[]] | unique | length),
    senior_roles: ([.employees[] | select(.role | contains(\"Senior\") or contains(\"Lead\") or contains(\"Director\") or contains(\"Manager\"))] | length)
  })"
}

# Example 2: Time series data processing
data "pyvider_lens_jq" "metrics_analysis" {
  json_input = jsonencode({
    metrics = [
      { timestamp = "2024-01-01T00:00:00Z", cpu_usage = 45.2, memory_usage = 67.8, requests = 1250 },
      { timestamp = "2024-01-01T01:00:00Z", cpu_usage = 52.1, memory_usage = 72.1, requests = 1380 },
      { timestamp = "2024-01-01T02:00:00Z", cpu_usage = 38.9, memory_usage = 65.2, requests = 1100 },
      { timestamp = "2024-01-01T03:00:00Z", cpu_usage = 61.7, memory_usage = 78.9, requests = 1520 },
      { timestamp = "2024-01-01T04:00:00Z", cpu_usage = 44.3, memory_usage = 69.4, requests = 1290 }
    ]
  })
  query = "{
    total_hours: (.metrics | length),
    cpu_stats: {
      average: (([.metrics[].cpu_usage] | add) / (.metrics | length)),
      max: ([.metrics[].cpu_usage] | max),
      min: ([.metrics[].cpu_usage] | min),
      above_50: ([.metrics[] | select(.cpu_usage > 50)] | length)
    },
    memory_stats: {
      average: (([.metrics[].memory_usage] | add) / (.metrics | length)),
      max: ([.metrics[].memory_usage] | max),
      min: ([.metrics[].memory_usage] | min),
      above_75: ([.metrics[] | select(.memory_usage > 75)] | length)
    },
    request_stats: {
      total: ([.metrics[].requests] | add),
      average: (([.metrics[].requests] | add) / (.metrics | length)),
      peak_hour: (.metrics | max_by(.requests) | .timestamp),
      low_hour: (.metrics | min_by(.requests) | .timestamp)
    },
    alerts: [
      (.metrics[] | select(.cpu_usage > 60) | \"High CPU at \" + .timestamp),
      (.metrics[] | select(.memory_usage > 75) | \"High Memory at \" + .timestamp)
    ]
  }"
}

# Example 3: Configuration transformation and validation
data "pyvider_lens_jq" "config_processor" {
  json_input = jsonencode({
    environments = {
      development = {
        api_endpoint = "https://dev-api.example.com"
        database_url = "postgres://dev-db:5432/app"
        redis_url = "redis://dev-cache:6379"
        log_level = "debug"
        replicas = 1
        resources = {
          cpu = "100m"
          memory = "256Mi"
        }
      }
      staging = {
        api_endpoint = "https://staging-api.example.com"
        database_url = "postgres://staging-db:5432/app"
        redis_url = "redis://staging-cache:6379"
        log_level = "info"
        replicas = 2
        resources = {
          cpu = "500m"
          memory = "512Mi"
        }
      }
      production = {
        api_endpoint = "https://api.example.com"
        database_url = "postgres://prod-db:5432/app"
        redis_url = "redis://prod-cache:6379"
        log_level = "warn"
        replicas = 5
        resources = {
          cpu = "1000m"
          memory = "1Gi"
        }
      }
    }
  })
  query = ".environments | to_entries | map({
    environment: .key,
    config: .value,
    security_score: (
      (if (.value.api_endpoint | startswith(\"https://\")) then 25 else 0 end) +
      (if (.value.database_url | contains(\"ssl\")) then 25 else 10 end) +
      (if (.value.log_level == \"warn\" or .value.log_level == \"error\") then 25 else 0 end) +
      (if (.value.replicas > 1) then 25 else 0 end)
    ),
    resource_tier: (
      if (.value.resources.memory | test(\"Gi\")) then \"high\"
      elif (.value.resources.memory | test(\"512Mi\")) then \"medium\"
      else \"low\"
      end
    ),
    recommendations: [
      (if (.value.log_level == \"debug\" and .key != \"development\") then \"Consider changing log level from debug\" else empty end),
      (if (.value.replicas < 2 and .key == \"production\") then \"Production should have multiple replicas\" else empty end),
      (if (.value.api_endpoint | startswith(\"http://\")) then \"Use HTTPS for secure communication\" else empty end)
    ]
  })"
}

# Example 4: Data aggregation and grouping
data "pyvider_lens_jq" "transaction_analysis" {
  json_input = jsonencode([
    { id = "tx1", amount = 150.50, currency = "USD", category = "food", date = "2024-01-15", user_id = "user1" },
    { id = "tx2", amount = 75.25, currency = "USD", category = "transport", date = "2024-01-15", user_id = "user2" },
    { id = "tx3", amount = 200.00, currency = "EUR", category = "food", date = "2024-01-16", user_id = "user1" },
    { id = "tx4", amount = 50.75, currency = "USD", category = "entertainment", date = "2024-01-16", user_id = "user3" },
    { id = "tx5", amount = 120.30, currency = "EUR", category = "food", date = "2024-01-17", user_id = "user2" },
    { id = "tx6", amount = 90.45, currency = "USD", category = "transport", date = "2024-01-17", user_id = "user1" }
  ])
  query = "{
    by_category: (
      group_by(.category) | map({
        category: .[0].category,
        total_transactions: length,
        total_amount_usd: ([.[] | select(.currency == \"USD\") | .amount] | add // 0),
        total_amount_eur: ([.[] | select(.currency == \"EUR\") | .amount] | add // 0),
        avg_amount: (([.[].amount] | add) / length),
        users: ([.[].user_id] | unique)
      })
    ),
    by_currency: (
      group_by(.currency) | map({
        currency: .[0].currency,
        transaction_count: length,
        total_amount: ([.[].amount] | add),
        avg_amount: (([.[].amount] | add) / length),
        categories: ([.[].category] | unique)
      })
    ),
    by_date: (
      group_by(.date) | map({
        date: .[0].date,
        transaction_count: length,
        daily_total: ([.[].amount] | add),
        unique_users: ([.[].user_id] | unique | length)
      })
    ),
    summary: {
      total_transactions: length,
      unique_users: ([.[].user_id] | unique | length),
      date_range: {
        first: (map(.date) | sort | first),
        last: (map(.date) | sort | last)
      },
      largest_transaction: (max_by(.amount) | {id, amount, category}),
      most_active_user: (
        group_by(.user_id) | map({user: .[0].user_id, count: length}) | max_by(.count) | .user
      )
    }
  }"
}

# Create detailed analysis files
resource "pyvider_file_content" "company_analysis_report" {
  filename = "/tmp/company_analysis.json"
  content = jsonencode({
    timestamp = timestamp()
    analysis = jsondecode(data.pyvider_lens_jq.company_analysis.result)
    summary = {
      total_departments = length(jsondecode(data.pyvider_lens_jq.company_analysis.result))
      highest_budget_utilization = max([
        for dept in jsondecode(data.pyvider_lens_jq.company_analysis.result) :
        dept.budget_utilization
      ]...)
      most_diverse_skills = max([
        for dept in jsondecode(data.pyvider_lens_jq.company_analysis.result) :
        dept.skill_diversity
      ]...)
    }
  })
}

resource "pyvider_file_content" "metrics_dashboard" {
  filename = "/tmp/metrics_dashboard.txt"
  content = join("\n", [
    "=== System Metrics Dashboard ===",
    "",
    "Monitoring Period: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).total_hours} hours",
    "",
    "CPU Performance:",
    "- Average: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.average}%",
    "- Peak: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.max}%",
    "- High Usage Hours: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.above_50}",
    "",
    "Memory Performance:",
    "- Average: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.average}%",
    "- Peak: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.max}%",
    "- Critical Hours: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.above_75}",
    "",
    "Request Statistics:",
    "- Total Requests: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.total}",
    "- Average per Hour: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.average}",
    "- Peak Hour: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.peak_hour}",
    "",
    "Alerts Generated: ${length(jsondecode(data.pyvider_lens_jq.metrics_analysis.result).alerts)}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Output comprehensive results
output "complex_jq_analysis" {
  description = "Complex JQ transformation results"
  value = {
    company_analysis = {
      departments_analyzed = length(jsondecode(data.pyvider_lens_jq.company_analysis.result))
      total_employees = sum([
        for dept in jsondecode(data.pyvider_lens_jq.company_analysis.result) :
        dept.employee_count
      ])
    }

    metrics_summary = {
      monitoring_hours = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).total_hours
      cpu_avg = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.average
      memory_avg = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.average
      total_requests = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.total
      alerts_generated = length(jsondecode(data.pyvider_lens_jq.metrics_analysis.result).alerts)
    }

    config_environments = length(jsondecode(data.pyvider_lens_jq.config_processor.result))

    transaction_summary = {
      total_transactions = jsondecode(data.pyvider_lens_jq.transaction_analysis.result).summary.total_transactions
      unique_users = jsondecode(data.pyvider_lens_jq.transaction_analysis.result).summary.unique_users
      categories_found = length(jsondecode(data.pyvider_lens_jq.transaction_analysis.result).by_category)
      currencies_found = length(jsondecode(data.pyvider_lens_jq.transaction_analysis.result).by_currency)
    }

    files_created = [
      pyvider_file_content.company_analysis_report.filename,
      pyvider_file_content.metrics_dashboard.filename
    ]
  }
}