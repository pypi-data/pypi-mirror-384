---
page_title: "Resource: pyvider_private_state_verifier"
description: |-
  Verifies private state encryption and decryption functionality in Terraform resources
---

# pyvider_private_state_verifier (Resource)

> Verify and test private state encryption mechanisms in Terraform provider development

The `pyvider_private_state_verifier` resource is designed for testing and verifying the private state encryption functionality of Terraform providers. It demonstrates how sensitive data can be securely stored in private state, encrypted by Terraform, and properly decrypted when needed.

## When to Use This

- **Provider development**: Test private state encryption during provider development
- **Security validation**: Verify that sensitive data is properly encrypted in state
- **Testing workflows**: Validate encryption/decryption cycles in CI/CD pipelines
- **Compliance verification**: Ensure private state handling meets security requirements
- **Educational purposes**: Learn how Terraform private state encryption works

**Anti-patterns (when NOT to use):**
- Production workloads (this is a testing/verification resource)
- Storing actual secrets (use proper secret management systems)
- General-purpose encryption (use dedicated encryption tools)
- Long-term data storage (this is for verification only)

## Quick Start

```terraform
# Basic private state verification
resource "pyvider_private_state_verifier" "test" {
  input_value = "test-data"
}

# Verify the decryption works
output "verification_result" {
  value = pyvider_private_state_verifier.test.decrypted_token
}
```

## Examples

### Basic Usage

{{ example("basic") }}

### Security Testing

{{ example("security_testing") }}

### Compliance Verification

{{ example("compliance") }}

### CI/CD Integration

{{ example("cicd_testing") }}

## Schema

{{ schema() }}

## How Private State Verification Works

The `pyvider_private_state_verifier` resource demonstrates the complete lifecycle of private state encryption:

### 1. Creation Phase
- Takes an `input_value` as configuration
- Generates a secret token based on the input: `SECRET_FOR_{INPUT_VALUE_UPPER}`
- Stores the secret token in encrypted private state
- Returns a planned state with the decrypted token marked as computed

### 2. Apply Phase
- Retrieves the encrypted private state
- Terraform automatically decrypts the private state
- Populates the `decrypted_token` attribute with the decrypted value
- Validates that the decryption process worked correctly

### 3. Read Phase
- Returns the current state including the decrypted token
- Demonstrates that private state persists across operations
- Shows that encrypted data remains accessible when needed

### 4. Verification
- Compares input and output to ensure encryption/decryption cycle worked
- Validates that sensitive data was never stored in plain text in the state file
- Confirms that Terraform's encryption mechanisms are functioning

## Security Features

### Private State Encryption
```terraform
resource "pyvider_private_state_verifier" "encryption_test" {
  input_value = "sensitive-data"
}

# The actual secret token is encrypted in private state
# Only the decrypted result is available as an attribute
output "encryption_works" {
  value = pyvider_private_state_verifier.encryption_test.decrypted_token
  # Will output: "SECRET_FOR_SENSITIVE-DATA"
}
```

### State File Security
- **Input data**: Stored in regular state (visible)
- **Secret generation**: Happens during resource creation
- **Secret storage**: Encrypted in private state (not visible in state file)
- **Decrypted output**: Available as computed attribute

### Verification Pattern
```terraform
locals {
  test_input = "my-test-value"
  expected_secret = "SECRET_FOR_${upper(local.test_input)}"
}

resource "pyvider_private_state_verifier" "verify" {
  input_value = local.test_input
}

# Verify the encryption/decryption cycle worked
output "verification_passed" {
  value = pyvider_private_state_verifier.verify.decrypted_token == local.expected_secret
}
```

## Common Patterns

### Testing Multiple Scenarios
```terraform
# Test different input types
resource "pyvider_private_state_verifier" "alphanumeric" {
  input_value = "test123"
}

resource "pyvider_private_state_verifier" "special_chars" {
  input_value = "test-with-dashes"
}

resource "pyvider_private_state_verifier" "long_input" {
  input_value = "this-is-a-very-long-test-input-value-for-verification"
}

# Verify all tests pass
locals {
  all_tests_pass = (
    pyvider_private_state_verifier.alphanumeric.decrypted_token == "SECRET_FOR_TEST123" &&
    pyvider_private_state_verifier.special_chars.decrypted_token == "SECRET_FOR_TEST-WITH-DASHES" &&
    pyvider_private_state_verifier.long_input.decrypted_token == "SECRET_FOR_THIS-IS-A-VERY-LONG-TEST-INPUT-VALUE-FOR-VERIFICATION"
  )
}
```

### Compliance Testing Framework
```terraform
variable "compliance_tests" {
  description = "List of compliance test scenarios"
  type = list(object({
    name = string
    input = string
    category = string
  }))
  default = [
    {
      name = "basic_encryption"
      input = "basic-test"
      category = "functionality"
    },
    {
      name = "special_characters"
      input = "special!@#$%"
      category = "edge_cases"
    },
    {
      name = "unicode_support"
      input = "unicode-тест-测试"
      category = "internationalization"
    }
  ]
}

resource "pyvider_private_state_verifier" "compliance_test" {
  for_each = {
    for test in var.compliance_tests : test.name => test
  }

  input_value = each.value.input
}

# Generate compliance report
locals {
  compliance_results = {
    for test_name, test_config in var.compliance_tests :
    test_name => {
      input = test_config.input
      expected = "SECRET_FOR_${upper(test_config.input)}"
      actual = pyvider_private_state_verifier.compliance_test[test_name].decrypted_token
      passed = pyvider_private_state_verifier.compliance_test[test_name].decrypted_token == "SECRET_FOR_${upper(test_config.input)}"
      category = test_config.category
    }
  }
}
```

### CI/CD Verification Pipeline
```terraform
# Automated testing resource
resource "pyvider_private_state_verifier" "ci_test" {
  input_value = "ci-pipeline-test-${formatdate("YYYY-MM-DD", timestamp())}"
}

# Create test report for CI/CD
resource "pyvider_file_content" "ci_test_report" {
  filename = "/tmp/private_state_test_report.json"
  content = jsonencode({
    test_run = {
      timestamp = timestamp()
      test_name = "private_state_encryption_verification"
      input_value = pyvider_private_state_verifier.ci_test.input_value
      decrypted_token = pyvider_private_state_verifier.ci_test.decrypted_token
      expected_pattern = "SECRET_FOR_*"
      test_passed = can(regex("^SECRET_FOR_", pyvider_private_state_verifier.ci_test.decrypted_token))
    }

    security_validation = {
      private_state_used = true
      encryption_verified = true
      state_file_protection = true
      decryption_successful = pyvider_private_state_verifier.ci_test.decrypted_token != null
    }
  })
}
```

### Integration with Other Resources
```terraform
# Use with timed tokens for comprehensive testing
resource "pyvider_timed_token" "test_token" {
  name = "verification-test-token"
}

resource "pyvider_private_state_verifier" "integrated_test" {
  input_value = "integration-with-${pyvider_timed_token.test_token.id}"
}

# Verify both resources work together
locals {
  integration_test_passed = (
    pyvider_timed_token.test_token.id != null &&
    pyvider_private_state_verifier.integrated_test.decrypted_token != null &&
    can(regex("SECRET_FOR_INTEGRATION-WITH-", pyvider_private_state_verifier.integrated_test.decrypted_token))
  )
}
```

## Error Handling and Validation

### Input Validation
```terraform
variable "test_inputs" {
  description = "Test inputs for validation"
  type = list(string)
  default = ["valid-input", "another-test"]

  validation {
    condition = alltrue([
      for input in var.test_inputs : length(input) > 0
    ])
    error_message = "All test inputs must be non-empty strings."
  }
}

resource "pyvider_private_state_verifier" "validated_test" {
  for_each = toset(var.test_inputs)

  input_value = each.value
}
```

### Failure Detection
```terraform
resource "pyvider_private_state_verifier" "failure_test" {
  input_value = "failure-detection-test"
}

# Check for common failure scenarios
locals {
  test_failures = [
    {
      name = "null_decrypted_token"
      failed = pyvider_private_state_verifier.failure_test.decrypted_token == null
      message = "Decrypted token is null"
    },
    {
      name = "empty_decrypted_token"
      failed = pyvider_private_state_verifier.failure_test.decrypted_token == ""
      message = "Decrypted token is empty"
    },
    {
      name = "incorrect_format"
      failed = !can(regex("^SECRET_FOR_", pyvider_private_state_verifier.failure_test.decrypted_token))
      message = "Decrypted token doesn't match expected format"
    }
  ]

  any_failures = anytrue([for failure in local.test_failures : failure.failed])
  failure_messages = [for failure in local.test_failures : failure.message if failure.failed]
}
```

## Best Practices

### 1. Meaningful Test Names
```terraform
# ✅ Good - descriptive test names
resource "pyvider_private_state_verifier" "user_id_encryption" {
  input_value = "user-12345"
}

resource "pyvider_private_state_verifier" "api_key_verification" {
  input_value = "api-key-test"
}

# ❌ Bad - generic names
resource "pyvider_private_state_verifier" "test1" {
  input_value = "something"
}
```

### 2. Comprehensive Test Coverage
```terraform
# Test various input scenarios
locals {
  test_scenarios = {
    empty_string = ""
    single_char = "a"
    numbers_only = "12345"
    mixed_case = "MixedCase"
    special_chars = "test!@#$%^&*()"
    unicode = "测试-тест-テスト"
    very_long = join("", [for i in range(100) : "a"])
  }
}

resource "pyvider_private_state_verifier" "comprehensive_test" {
  for_each = local.test_scenarios

  input_value = each.value
}
```

### 3. Documentation and Reporting
```terraform
resource "pyvider_private_state_verifier" "documented_test" {
  input_value = "production-readiness-test"

  lifecycle {
    # Document the purpose of this test
    # This verifies that private state encryption works correctly
    # before deploying to production environments
    ignore_changes = []
  }
}

# Generate documentation
resource "pyvider_file_content" "test_documentation" {
  filename = "/tmp/private_state_test_docs.md"
  content = join("\n", [
    "# Private State Encryption Test Documentation",
    "",
    "## Test Purpose",
    "Verify that Terraform private state encryption is working correctly.",
    "",
    "## Test Input",
    "Input Value: `${pyvider_private_state_verifier.documented_test.input_value}`",
    "",
    "## Test Results",
    "Decrypted Token: `${pyvider_private_state_verifier.documented_test.decrypted_token}`",
    "",
    "## Verification",
    "Expected Pattern: `SECRET_FOR_{UPPER_INPUT}`",
    "Test Passed: ${can(regex("^SECRET_FOR_", pyvider_private_state_verifier.documented_test.decrypted_token))}",
    "",
    "## Security Notes",
    "- The secret token is stored in encrypted private state",
    "- The input value is visible in regular state",
    "- The decrypted token is available as a computed attribute",
    "- No sensitive data is exposed in the state file",
    "",
    "Generated: ${timestamp()}"
  ])
}
```

### 4. Environment-Specific Testing
```terraform
variable "environment" {
  description = "Environment for testing"
  type = string
  default = "development"
}

resource "pyvider_private_state_verifier" "env_specific_test" {
  input_value = "${var.environment}-encryption-test"
}

# Environment-specific validation
locals {
  env_test_passed = pyvider_private_state_verifier.env_specific_test.decrypted_token == "SECRET_FOR_${upper(var.environment)}-ENCRYPTION-TEST"

  production_ready = var.environment == "production" ? local.env_test_passed : true
}
```

## Troubleshooting

### Common Issues

**Issue**: Decrypted token is null
**Cause**: Private state was not properly created or encryption failed
**Solution**: Check provider logs and ensure private state support is enabled

**Issue**: Decrypted token doesn't match expected format
**Cause**: Secret generation logic may have changed
**Solution**: Verify the expected format: `SECRET_FOR_{UPPER_INPUT_VALUE}`

**Issue**: State file shows encrypted data
**Cause**: Data may not be properly stored in private state
**Solution**: Ensure the resource uses `PrivateState` class correctly

### Debugging Techniques
```terraform
resource "pyvider_private_state_verifier" "debug_test" {
  input_value = "debug-test-value"
}

# Debug output (be careful not to expose in production)
output "debug_info" {
  value = {
    input_provided = pyvider_private_state_verifier.debug_test.input_value
    output_received = pyvider_private_state_verifier.debug_test.decrypted_token
    output_length = length(pyvider_private_state_verifier.debug_test.decrypted_token)
    format_correct = can(regex("^SECRET_FOR_", pyvider_private_state_verifier.debug_test.decrypted_token))
  }
}
```

## Related Components

- [`pyvider_timed_token`](../timed_token.md) - Time-limited tokens with private state
- [`pyvider_file_content`](../file_content.md) - Create test reports and documentation
- [`pyvider_warning_example`](../warning_example.md) - Testing warning mechanisms