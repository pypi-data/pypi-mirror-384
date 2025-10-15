# Basic provider configuration reader examples

# Example 1: Read current provider configuration
data "pyvider_provider_config_reader" "current" {}

# Example 2: Use provider configuration in file creation
resource "pyvider_file_content" "provider_summary" {
  filename = "/tmp/provider_config_summary.txt"
  content = join("\n", [
    "=== Provider Configuration Summary ===",
    "",
    "API Endpoint: ${data.pyvider_provider_config_reader.current.api_endpoint != null ? data.pyvider_provider_config_reader.current.api_endpoint : "Not configured"}",
    "API Timeout: ${data.pyvider_provider_config_reader.current.api_timeout != null ? "${data.pyvider_provider_config_reader.current.api_timeout} seconds" : "Default"}",
    "API Retries: ${data.pyvider_provider_config_reader.current.api_retries != null ? data.pyvider_provider_config_reader.current.api_retries : "Default"}",
    "TLS Verification: ${data.pyvider_provider_config_reader.current.api_insecure_skip_verify != null ? (data.pyvider_provider_config_reader.current.api_insecure_skip_verify ? "DISABLED" : "ENABLED") : "Default (enabled)"}",
    "Authentication: ${data.pyvider_provider_config_reader.current.api_token != null ? "Token configured" : "No authentication"}",
    "Custom Headers: ${data.pyvider_provider_config_reader.current.api_headers != null ? length(data.pyvider_provider_config_reader.current.api_headers) : 0} headers",
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Example 3: Create environment detection based on provider config
locals {
  # Determine environment from API endpoint
  detected_environment = (
    data.pyvider_provider_config_reader.current.api_endpoint != null ? (
      can(regex("localhost|127\\.0\\.0\\.1", data.pyvider_provider_config_reader.current.api_endpoint)) ? "local" :
      can(regex("dev|development", data.pyvider_provider_config_reader.current.api_endpoint)) ? "development" :
      can(regex("test|testing", data.pyvider_provider_config_reader.current.api_endpoint)) ? "testing" :
      can(regex("staging|stage", data.pyvider_provider_config_reader.current.api_endpoint)) ? "staging" :
      can(regex("prod|production", data.pyvider_provider_config_reader.current.api_endpoint)) ? "production" :
      "unknown"
    ) : "unconfigured"
  )

  # Configuration analysis
  config_analysis = {
    endpoint_configured = data.pyvider_provider_config_reader.current.api_endpoint != null
    auth_configured     = data.pyvider_provider_config_reader.current.api_token != null
    has_custom_headers  = data.pyvider_provider_config_reader.current.api_headers != null && length(data.pyvider_provider_config_reader.current.api_headers) > 0
    tls_secure         = data.pyvider_provider_config_reader.current.api_insecure_skip_verify != true

    timeout_configured = data.pyvider_provider_config_reader.current.api_timeout != null
    timeout_value     = data.pyvider_provider_config_reader.current.api_timeout
    timeout_category  = (
      data.pyvider_provider_config_reader.current.api_timeout == null ? "default" :
      data.pyvider_provider_config_reader.current.api_timeout <= 10 ? "fast" :
      data.pyvider_provider_config_reader.current.api_timeout <= 60 ? "normal" :
      data.pyvider_provider_config_reader.current.api_timeout <= 300 ? "slow" :
      "very_slow"
    )

    retries_configured = data.pyvider_provider_config_reader.current.api_retries != null
    retries_value     = data.pyvider_provider_config_reader.current.api_retries
    retries_category  = (
      data.pyvider_provider_config_reader.current.api_retries == null ? "default" :
      data.pyvider_provider_config_reader.current.api_retries == 0 ? "no_retries" :
      data.pyvider_provider_config_reader.current.api_retries <= 3 ? "conservative" :
      data.pyvider_provider_config_reader.current.api_retries <= 10 ? "aggressive" :
      "very_aggressive"
    )
  }

  # Configuration recommendations
  config_recommendations = concat(
    !local.config_analysis.endpoint_configured ? ["Configure api_endpoint in provider block"] : [],
    !local.config_analysis.auth_configured ? ["Consider configuring api_token for authentication"] : [],
    !local.config_analysis.tls_secure ? ["WARNING: TLS verification is disabled - security risk"] : [],
    local.config_analysis.timeout_category == "very_slow" ? ["Consider reducing api_timeout for better performance"] : [],
    local.config_analysis.retries_category == "very_aggressive" ? ["High retry count may cause long delays on failures"] : []
  )

  # Security assessment
  security_score = (
    (local.config_analysis.endpoint_configured && can(regex("^https://", data.pyvider_provider_config_reader.current.api_endpoint)) ? 25 : 0) +
    (local.config_analysis.auth_configured ? 25 : 0) +
    (local.config_analysis.tls_secure ? 25 : 0) +
    (!local.config_analysis.has_custom_headers || length(data.pyvider_provider_config_reader.current.api_headers) <= 5 ? 25 : 0)
  )
}

# Example 4: Create environment-specific configuration file
resource "pyvider_file_content" "environment_config" {
  filename = "/tmp/environment_config.json"
  content = jsonencode({
    detected_environment = local.detected_environment

    provider_config = {
      endpoint_url = data.pyvider_provider_config_reader.current.api_endpoint
      timeout_seconds = data.pyvider_provider_config_reader.current.api_timeout
      retry_count = data.pyvider_provider_config_reader.current.api_retries
      tls_verification = !data.pyvider_provider_config_reader.current.api_insecure_skip_verify
      authentication_enabled = data.pyvider_provider_config_reader.current.api_token != null
      custom_headers_count = data.pyvider_provider_config_reader.current.api_headers != null ? length(data.pyvider_provider_config_reader.current.api_headers) : 0
    }

    analysis = local.config_analysis

    security = {
      score = local.security_score
      level = (
        local.security_score >= 75 ? "high" :
        local.security_score >= 50 ? "medium" :
        local.security_score >= 25 ? "low" :
        "very_low"
      )
    }

    recommendations = local.config_recommendations

    timestamp = timestamp()
  })
}

# Example 5: Conditional resource creation based on provider config
resource "pyvider_file_content" "debug_info" {
  count = local.detected_environment == "development" || local.detected_environment == "local" ? 1 : 0

  filename = "/tmp/debug_info.txt"
  content = join("\n", [
    "=== DEBUG MODE ENABLED ===",
    "Environment: ${local.detected_environment}",
    "Provider endpoint: ${data.pyvider_provider_config_reader.current.api_endpoint}",
    "Timeout configuration: ${local.config_analysis.timeout_category}",
    "Retry configuration: ${local.config_analysis.retries_category}",
    "Security score: ${local.security_score}/100",
    "",
    "This file is only created in development/local environments.",
    "Generated at: ${timestamp()}"
  ])
}

resource "pyvider_file_content" "production_config" {
  count = local.detected_environment == "production" ? 1 : 0

  filename = "/tmp/production_config.txt"
  content = join("\n", [
    "=== PRODUCTION ENVIRONMENT DETECTED ===",
    "Security level: ${local.security_score >= 75 ? "ACCEPTABLE" : "NEEDS IMPROVEMENT"}",
    "TLS verification: ${local.config_analysis.tls_secure ? "ENABLED" : "DISABLED - SECURITY RISK"}",
    "Authentication: ${local.config_analysis.auth_configured ? "CONFIGURED" : "NOT CONFIGURED"}",
    "",
    length(local.config_recommendations) > 0 ? "RECOMMENDATIONS:" : "Configuration looks good!",
    join("\n", [for rec in local.config_recommendations : "- ${rec}"]),
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Example 6: Create API client configuration file
resource "pyvider_file_content" "api_client_config" {
  filename = "/tmp/api_client_config.yaml"
  content = yamlencode({
    api_client = {
      base_url = data.pyvider_provider_config_reader.current.api_endpoint != null ? data.pyvider_provider_config_reader.current.api_endpoint : "http://localhost:8080"

      timeout = {
        seconds = data.pyvider_provider_config_reader.current.api_timeout != null ? data.pyvider_provider_config_reader.current.api_timeout : 30
        category = local.config_analysis.timeout_category
      }

      retry_policy = {
        max_attempts = data.pyvider_provider_config_reader.current.api_retries != null ? data.pyvider_provider_config_reader.current.api_retries + 1 : 4
        strategy = local.config_analysis.retries_category
      }

      security = {
        verify_tls = !data.pyvider_provider_config_reader.current.api_insecure_skip_verify
        auth_required = data.pyvider_provider_config_reader.current.api_token != null
      }

      headers = data.pyvider_provider_config_reader.current.api_headers != null ? data.pyvider_provider_config_reader.current.api_headers : {}
    }

    metadata = {
      environment = local.detected_environment
      security_score = local.security_score
      config_source = "terraform_provider"
      generated_at = timestamp()
    }
  })
}

output "provider_config_analysis" {
  description = "Analysis of current provider configuration"
  value = {
    detected_environment = local.detected_environment

    configuration = {
      endpoint_configured = local.config_analysis.endpoint_configured
      auth_configured = local.config_analysis.auth_configured
      tls_secure = local.config_analysis.tls_secure
      timeout_category = local.config_analysis.timeout_category
      retries_category = local.config_analysis.retries_category
    }

    security = {
      score = local.security_score
      level = (
        local.security_score >= 75 ? "high" :
        local.security_score >= 50 ? "medium" :
        local.security_score >= 25 ? "low" :
        "very_low"
      )
    }

    recommendations_count = length(local.config_recommendations)

    files_created = concat(
      [
        pyvider_file_content.provider_summary.filename,
        pyvider_file_content.environment_config.filename,
        pyvider_file_content.api_client_config.filename
      ],
      local.detected_environment == "development" || local.detected_environment == "local" ? [
        pyvider_file_content.debug_info[0].filename
      ] : [],
      local.detected_environment == "production" ? [
        pyvider_file_content.production_config[0].filename
      ] : []
    )
  }
}