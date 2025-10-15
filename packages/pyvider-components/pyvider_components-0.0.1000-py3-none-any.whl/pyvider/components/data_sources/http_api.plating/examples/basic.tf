# Basic HTTP API usage examples

# Example 1: Simple GET request
data "pyvider_http_api" "simple_get" {
  url = "https://httpbin.org/get"
}

# Example 2: GET request with query parameters in URL
data "pyvider_http_api" "with_params" {
  url = "https://httpbin.org/get?param1=value1&param2=value2"
}

# Example 3: GET request with custom headers
data "pyvider_http_api" "with_headers" {
  url = "https://httpbin.org/headers"
  headers = {
    "User-Agent"    = "Terraform-Pyvider/1.0"
    "Accept"        = "application/json"
    "Custom-Header" = "custom-value"
  }
}

# Example 4: Request with custom timeout
data "pyvider_http_api" "with_timeout" {
  url     = "https://httpbin.org/delay/2"
  timeout = 10  # 10 seconds
}

# Example 5: HEAD request to check resource existence
data "pyvider_http_api" "head_check" {
  url    = "https://httpbin.org/status/200"
  method = "HEAD"
}

# Example 6: Real-world example - GitHub API
data "pyvider_http_api" "github_user" {
  url = "https://api.github.com/users/octocat"
  headers = {
    "Accept"     = "application/vnd.github.v3+json"
    "User-Agent" = "Terraform-Provider-Example"
  }
}

# Example 7: JSONPlaceholder API for testing
data "pyvider_http_api" "json_placeholder" {
  url = "https://jsonplaceholder.typicode.com/posts/1"
  headers = {
    "Accept" = "application/json"
  }
}

# Process API responses
locals {
  # Parse JSON responses
  github_user = can(jsondecode(data.pyvider_http_api.github_user.response_body)) ?
    jsondecode(data.pyvider_http_api.github_user.response_body) : {}

  json_post = can(jsondecode(data.pyvider_http_api.json_placeholder.response_body)) ?
    jsondecode(data.pyvider_http_api.json_placeholder.response_body) : {}

  # Extract specific information
  user_info = {
    name         = lookup(local.github_user, "name", "Unknown")
    public_repos = lookup(local.github_user, "public_repos", 0)
    followers    = lookup(local.github_user, "followers", 0)
    company      = lookup(local.github_user, "company", "None")
  }

  post_info = {
    title  = lookup(local.json_post, "title", "No title")
    body   = lookup(local.json_post, "body", "No content")
    userId = lookup(local.json_post, "userId", 0)
  }

  # Check response success
  requests_status = {
    simple_get = {
      success       = data.pyvider_http_api.simple_get.status_code == 200
      response_time = data.pyvider_http_api.simple_get.response_time_ms
      content_type  = data.pyvider_http_api.simple_get.content_type
    }

    github_api = {
      success       = data.pyvider_http_api.github_user.status_code == 200
      response_time = data.pyvider_http_api.github_user.response_time_ms
      headers_count = data.pyvider_http_api.github_user.header_count
    }

    head_request = {
      success       = data.pyvider_http_api.head_check.status_code == 200
      response_time = data.pyvider_http_api.head_check.response_time_ms
      has_body      = data.pyvider_http_api.head_check.response_body != null
    }
  }
}

# Create files with API responses
resource "pyvider_file_content" "api_responses" {
  filename = "/tmp/http_api_basic_responses.json"
  content = jsonencode({
    timestamp = timestamp()

    responses = {
      simple_get = {
        url         = data.pyvider_http_api.simple_get.url
        status_code = data.pyvider_http_api.simple_get.status_code
        success     = local.requests_status.simple_get.success
        response_time_ms = data.pyvider_http_api.simple_get.response_time_ms
        content_type = data.pyvider_http_api.simple_get.content_type
      }

      with_headers = {
        url           = data.pyvider_http_api.with_headers.url
        status_code   = data.pyvider_http_api.with_headers.status_code
        headers_count = data.pyvider_http_api.with_headers.header_count
      }

      timeout_test = {
        url           = data.pyvider_http_api.with_timeout.url
        status_code   = data.pyvider_http_api.with_timeout.status_code
        response_time = data.pyvider_http_api.with_timeout.response_time_ms
        configured_timeout = 10
      }

      head_request = {
        url         = data.pyvider_http_api.head_check.url
        method      = data.pyvider_http_api.head_check.method
        status_code = data.pyvider_http_api.head_check.status_code
        has_body    = local.requests_status.head_request.has_body
      }
    }

    parsed_data = {
      github_user = local.user_info
      sample_post = local.post_info
    }

    performance_summary = {
      total_requests = 7
      successful_requests = length([
        for status in values(local.requests_status) : status
        if status.success
      ])
      average_response_time = (
        data.pyvider_http_api.simple_get.response_time_ms +
        data.pyvider_http_api.github_user.response_time_ms +
        data.pyvider_http_api.head_check.response_time_ms
      ) / 3
    }
  })
}

# Create a simple text report
resource "pyvider_file_content" "api_report" {
  filename = "/tmp/http_api_basic_report.txt"
  content = join("\n", [
    "=== HTTP API Basic Examples Report ===",
    "",
    "=== Request Status Summary ===",
    "Simple GET: ${local.requests_status.simple_get.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.simple_get.status_code}) - ${data.pyvider_http_api.simple_get.response_time_ms}ms",
    "With Headers: ${data.pyvider_http_api.with_headers.status_code == 200 ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.with_headers.status_code}) - ${data.pyvider_http_api.with_headers.header_count} headers",
    "Timeout Test: ${local.requests_status.simple_get.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.with_timeout.status_code}) - ${data.pyvider_http_api.with_timeout.response_time_ms}ms",
    "HEAD Request: ${local.requests_status.head_request.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.head_check.status_code}) - No body: ${!local.requests_status.head_request.has_body}",
    "GitHub API: ${local.requests_status.github_api.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.github_user.status_code}) - ${data.pyvider_http_api.github_user.response_time_ms}ms",
    "",
    "=== GitHub User Information ===",
    "Name: ${local.user_info.name}",
    "Public Repos: ${local.user_info.public_repos}",
    "Followers: ${local.user_info.followers}",
    "Company: ${local.user_info.company}",
    "",
    "=== Sample Post Information ===",
    "Title: ${local.post_info.title}",
    "User ID: ${local.post_info.userId}",
    "Content Length: ${length(local.post_info.body)} characters",
    "",
    "=== Performance Metrics ===",
    "Fastest Response: ${min(data.pyvider_http_api.simple_get.response_time_ms, data.pyvider_http_api.github_user.response_time_ms, data.pyvider_http_api.head_check.response_time_ms)}ms",
    "Slowest Response: ${max(data.pyvider_http_api.simple_get.response_time_ms, data.pyvider_http_api.github_user.response_time_ms, data.pyvider_http_api.head_check.response_time_ms)}ms",
    "",
    "Report generated at: ${timestamp()}"
  ])
}

output "basic_http_api_results" {
  description = "Results from basic HTTP API calls"
  value = {
    request_summary = {
      total_requests = 7
      successful_requests = length([
        for req in [
          data.pyvider_http_api.simple_get,
          data.pyvider_http_api.with_headers,
          data.pyvider_http_api.with_timeout,
          data.pyvider_http_api.head_check,
          data.pyvider_http_api.github_user,
          data.pyvider_http_api.json_placeholder
        ] : req if req.status_code == 200
      ])
    }

    response_times = {
      simple_get   = data.pyvider_http_api.simple_get.response_time_ms
      github_api   = data.pyvider_http_api.github_user.response_time_ms
      head_request = data.pyvider_http_api.head_check.response_time_ms
    }

    parsed_data = {
      github_user = local.user_info
      sample_post = local.post_info
    }

    content_types = {
      simple_get    = data.pyvider_http_api.simple_get.content_type
      github_api    = data.pyvider_http_api.github_user.content_type
      json_placeholder = data.pyvider_http_api.json_placeholder.content_type
    }

    generated_files = [
      pyvider_file_content.api_responses.filename,
      pyvider_file_content.api_report.filename
    ]
  }
}