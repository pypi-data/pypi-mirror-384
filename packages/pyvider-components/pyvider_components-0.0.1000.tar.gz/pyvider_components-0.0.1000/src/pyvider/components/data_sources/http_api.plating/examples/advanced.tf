# Advanced HTTP API usage examples

# Example 1: POST request with JSON content type
data "pyvider_http_api" "post_json" {
  url    = "https://httpbin.org/post"
  method = "POST"
  headers = {
    "Content-Type" = "application/json"
    "Accept"       = "application/json"
    "User-Agent"   = "Terraform-Pyvider-Advanced/1.0"
  }
}

# Example 2: PUT request for updates
data "pyvider_http_api" "put_request" {
  url    = "https://httpbin.org/put"
  method = "PUT"
  headers = {
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer fake-token-for-example"
    "X-Request-ID"  = "req-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  }
}

# Example 3: DELETE request
data "pyvider_http_api" "delete_request" {
  url    = "https://httpbin.org/delete"
  method = "DELETE"
  headers = {
    "Authorization" = "Bearer fake-token-for-example"
    "X-Reason"      = "cleanup-operation"
  }
}

# Example 4: PATCH request for partial updates
data "pyvider_http_api" "patch_request" {
  url    = "https://httpbin.org/patch"
  method = "PATCH"
  headers = {
    "Content-Type" = "application/json-patch+json"
    "If-Match"     = "etag-example"
  }
}

# Example 5: OPTIONS request to check allowed methods
data "pyvider_http_api" "options_request" {
  url    = "https://httpbin.org/get"
  method = "OPTIONS"
}

# Example 6: Request with custom timeout for slow APIs
data "pyvider_http_api" "slow_api" {
  url     = "https://httpbin.org/delay/3"
  timeout = 10
  headers = {
    "Accept-Encoding" = "gzip, deflate"
    "Cache-Control"   = "no-cache"
  }
}

# Example 7: Complex headers for API authentication
data "pyvider_http_api" "authenticated_api" {
  url = "https://httpbin.org/bearer"
  headers = {
    "Authorization"     = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example"
    "X-API-Version"     = "2023-01-01"
    "X-Client-Version"  = "terraform-provider-pyvider/1.0"
    "Accept"            = "application/vnd.api+json"
    "Content-Type"      = "application/vnd.api+json"
    "X-Request-Timeout" = "30"
  }
}

# Example 8: Multiple related API calls
data "pyvider_http_api" "user_profile" {
  url = "https://jsonplaceholder.typicode.com/users/1"
}

# Get posts for the user (using data from first call)
locals {
  user_data = can(jsondecode(data.pyvider_http_api.user_profile.response_body)) ?
    jsondecode(data.pyvider_http_api.user_profile.response_body) : { id = 1 }
}

data "pyvider_http_api" "user_posts" {
  url = "https://jsonplaceholder.typicode.com/posts?userId=${local.user_data.id}"
}

# Example 9: Error status code handling
data "pyvider_http_api" "not_found" {
  url = "https://httpbin.org/status/404"
}

data "pyvider_http_api" "server_error" {
  url = "https://httpbin.org/status/500"
}

data "pyvider_http_api" "unauthorized" {
  url = "https://httpbin.org/status/401"
}

# Process responses and handle different scenarios
locals {
  # Parse successful responses
  post_response = can(jsondecode(data.pyvider_http_api.post_json.response_body)) ?
    jsondecode(data.pyvider_http_api.post_json.response_body) : {}

  user_posts = can(jsondecode(data.pyvider_http_api.user_posts.response_body)) ?
    jsondecode(data.pyvider_http_api.user_posts.response_body) : []

  # Analyze response characteristics
  response_analysis = {
    post_request = {
      status_code   = data.pyvider_http_api.post_json.status_code
      response_time = data.pyvider_http_api.post_json.response_time_ms
      content_type  = data.pyvider_http_api.post_json.content_type
      headers_count = data.pyvider_http_api.post_json.header_count
      success       = data.pyvider_http_api.post_json.status_code >= 200 && data.pyvider_http_api.post_json.status_code < 300
    }

    put_request = {
      status_code   = data.pyvider_http_api.put_request.status_code
      response_time = data.pyvider_http_api.put_request.response_time_ms
      success       = data.pyvider_http_api.put_request.status_code >= 200 && data.pyvider_http_api.put_request.status_code < 300
    }

    delete_request = {
      status_code   = data.pyvider_http_api.delete_request.status_code
      response_time = data.pyvider_http_api.delete_request.response_time_ms
      success       = data.pyvider_http_api.delete_request.status_code >= 200 && data.pyvider_http_api.delete_request.status_code < 300
    }

    patch_request = {
      status_code   = data.pyvider_http_api.patch_request.status_code
      response_time = data.pyvider_http_api.patch_request.response_time_ms
      success       = data.pyvider_http_api.patch_request.status_code >= 200 && data.pyvider_http_api.patch_request.status_code < 300
    }

    options_request = {
      status_code   = data.pyvider_http_api.options_request.status_code
      response_time = data.pyvider_http_api.options_request.response_time_ms
      success       = data.pyvider_http_api.options_request.status_code == 200
    }

    slow_api = {
      status_code   = data.pyvider_http_api.slow_api.status_code
      response_time = data.pyvider_http_api.slow_api.response_time_ms
      timeout_ok    = data.pyvider_http_api.slow_api.response_time_ms <= 10000
      success       = data.pyvider_http_api.slow_api.status_code == 200
    }
  }

  # Error handling examples
  error_scenarios = {
    not_found = {
      status_code = data.pyvider_http_api.not_found.status_code
      is_404      = data.pyvider_http_api.not_found.status_code == 404
      has_error   = data.pyvider_http_api.not_found.error_message != null
    }

    server_error = {
      status_code = data.pyvider_http_api.server_error.status_code
      is_5xx      = data.pyvider_http_api.server_error.status_code >= 500
      has_error   = data.pyvider_http_api.server_error.error_message != null
    }

    unauthorized = {
      status_code = data.pyvider_http_api.unauthorized.status_code
      is_401      = data.pyvider_http_api.unauthorized.status_code == 401
      has_error   = data.pyvider_http_api.unauthorized.error_message != null
    }
  }

  # Performance metrics
  performance_metrics = {
    fastest_response = min([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ]...)

    slowest_response = max([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ]...)

    average_response_time = sum([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ]) / length([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ])

    success_rate = (length([
      for analysis in values(local.response_analysis) :
      analysis if analysis.success
    ]) / length(values(local.response_analysis))) * 100
  }
}

# Create comprehensive analysis file
resource "pyvider_file_content" "advanced_api_analysis" {
  filename = "/tmp/http_api_advanced_analysis.json"
  content = jsonencode({
    timestamp = timestamp()

    http_methods_tested = [
      "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
    ]

    response_analysis = local.response_analysis
    error_scenarios   = local.error_scenarios
    performance_metrics = local.performance_metrics

    user_data_example = {
      user_profile = local.user_data
      posts_count  = length(local.user_posts)
      first_post_title = length(local.user_posts) > 0 ? local.user_posts[0].title : null
    }

    api_patterns = {
      authentication_tested = true
      error_handling_tested = true
      timeout_handling_tested = true
      multiple_methods_tested = true
      json_responses_parsed = true
    }

    recommendations = [
      local.performance_metrics.success_rate < 100 ? "Some requests failed - check error handling" : null,
      local.performance_metrics.slowest_response > 5000 ? "Consider optimizing slow requests" : null,
      "Always implement proper error handling for production use",
      "Use environment variables for sensitive authentication tokens",
      "Consider implementing retry logic for critical API calls"
    ]
  })
}

# Create a detailed report
resource "pyvider_file_content" "advanced_api_report" {
  filename = "/tmp/http_api_advanced_report.txt"
  content = join("\n", [
    "=== Advanced HTTP API Examples Report ===",
    "",
    "=== HTTP Methods Test Results ===",
    "POST Request: ${local.response_analysis.post_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.post_request.status_code}) - ${local.response_analysis.post_request.response_time}ms",
    "PUT Request: ${local.response_analysis.put_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.put_request.status_code}) - ${local.response_analysis.put_request.response_time}ms",
    "DELETE Request: ${local.response_analysis.delete_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.delete_request.status_code}) - ${local.response_analysis.delete_request.response_time}ms",
    "PATCH Request: ${local.response_analysis.patch_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.patch_request.status_code}) - ${local.response_analysis.patch_request.response_time}ms",
    "OPTIONS Request: ${local.response_analysis.options_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.options_request.status_code}) - ${local.response_analysis.options_request.response_time}ms",
    "",
    "=== Timeout and Performance ===",
    "Slow API (3s delay): ${local.response_analysis.slow_api.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.slow_api.status_code}) - ${local.response_analysis.slow_api.response_time}ms",
    "Timeout handled correctly: ${local.response_analysis.slow_api.timeout_ok ? "YES" : "NO"}",
    "",
    "=== Error Handling Tests ===",
    "404 Not Found: Status ${local.error_scenarios.not_found.status_code} - Is 404: ${local.error_scenarios.not_found.is_404}",
    "500 Server Error: Status ${local.error_scenarios.server_error.status_code} - Is 5xx: ${local.error_scenarios.server_error.is_5xx}",
    "401 Unauthorized: Status ${local.error_scenarios.unauthorized.status_code} - Is 401: ${local.error_scenarios.unauthorized.is_401}",
    "",
    "=== Performance Summary ===",
    "Success Rate: ${local.performance_metrics.success_rate}%",
    "Fastest Response: ${local.performance_metrics.fastest_response}ms",
    "Slowest Response: ${local.performance_metrics.slowest_response}ms",
    "Average Response Time: ${local.performance_metrics.average_response_time}ms",
    "",
    "=== User Data Example ===",
    "User Name: ${lookup(local.user_data, "name", "Unknown")}",
    "User Email: ${lookup(local.user_data, "email", "Unknown")}",
    "Posts Count: ${length(local.user_posts)}",
    length(local.user_posts) > 0 ? "First Post: ${local.user_posts[0].title}" : "No posts found",
    "",
    "=== Content Types Observed ===",
    "POST Response: ${local.response_analysis.post_request.content_type}",
    "Headers Count (POST): ${local.response_analysis.post_request.headers_count}",
    "",
    "Report generated at: ${timestamp()}"
  ])
}

output "advanced_http_api_results" {
  description = "Results from advanced HTTP API operations"
  value = {
    methods_tested = {
      post    = local.response_analysis.post_request.success
      put     = local.response_analysis.put_request.success
      delete  = local.response_analysis.delete_request.success
      patch   = local.response_analysis.patch_request.success
      options = local.response_analysis.options_request.success
    }

    performance_summary = local.performance_metrics

    error_handling = {
      handled_404 = local.error_scenarios.not_found.is_404
      handled_500 = local.error_scenarios.server_error.is_5xx
      handled_401 = local.error_scenarios.unauthorized.is_401
    }

    data_processing = {
      user_profile_parsed = contains(keys(local.user_data), "name")
      posts_retrieved     = length(local.user_posts)
      json_parsing_works  = length(local.post_response) > 0
    }

    files_created = [
      pyvider_file_content.advanced_api_analysis.filename,
      pyvider_file_content.advanced_api_report.filename
    ]
  }
}