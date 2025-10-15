# Security-focused private state verification examples

# Example 1: Unicode and internationalization testing
resource "pyvider_private_state_verifier" "unicode_test" {
  input_value = "unicode-тест-测试-テスト"
}

# Example 2: Special characters and symbols
resource "pyvider_private_state_verifier" "symbols_test" {
  input_value = "symbols!@#$%^&*()_+-=[]{}|;:,.<>?"
}

# Example 3: SQL injection attempt simulation
resource "pyvider_private_state_verifier" "sql_injection_test" {
  input_value = "test'; DROP TABLE users; --"
}

# Example 4: XSS attempt simulation
resource "pyvider_private_state_verifier" "xss_test" {
  input_value = "<script>alert('xss')</script>"
}

# Example 5: Path traversal attempt simulation
resource "pyvider_private_state_verifier" "path_traversal_test" {
  input_value = "../../../etc/passwd"
}

# Example 6: Command injection attempt simulation
resource "pyvider_private_state_verifier" "command_injection_test" {
  input_value = "test; cat /etc/passwd"
}

# Example 7: Very long input (buffer overflow simulation)
resource "pyvider_private_state_verifier" "buffer_overflow_test" {
  input_value = join("", [for i in range(1000) : "A"])
}

# Example 8: Empty and whitespace testing
resource "pyvider_private_state_verifier" "empty_test" {
  input_value = ""
}

resource "pyvider_private_state_verifier" "whitespace_test" {
  input_value = "   spaces   and   tabs	"
}

# Example 9: Binary-like input
resource "pyvider_private_state_verifier" "binary_test" {
  input_value = "binary-001101001100001"
}

# Example 10: JSON-like input
resource "pyvider_private_state_verifier" "json_test" {
  input_value = "{\"malicious\":\"payload\"}"
}

# Security verification logic
locals {
  security_tests = {
    unicode = {
      input = pyvider_private_state_verifier.unicode_test.input_value
      output = pyvider_private_state_verifier.unicode_test.decrypted_token
      expected = "SECRET_FOR_UNICODE-ТЕСТ-测试-テスト"
      passed = pyvider_private_state_verifier.unicode_test.decrypted_token == "SECRET_FOR_UNICODE-ТЕСТ-测试-テスト"
      security_concern = "internationalization"
    }

    symbols = {
      input = pyvider_private_state_verifier.symbols_test.input_value
      output = pyvider_private_state_verifier.symbols_test.decrypted_token
      expected = "SECRET_FOR_SYMBOLS!@#$%^&*()_+-=[]{}|;:,.<>?"
      passed = pyvider_private_state_verifier.symbols_test.decrypted_token == "SECRET_FOR_SYMBOLS!@#$%^&*()_+-=[]{}|;:,.<>?"
      security_concern = "special_characters"
    }

    sql_injection = {
      input = pyvider_private_state_verifier.sql_injection_test.input_value
      output = pyvider_private_state_verifier.sql_injection_test.decrypted_token
      expected = "SECRET_FOR_TEST'; DROP TABLE USERS; --"
      passed = pyvider_private_state_verifier.sql_injection_test.decrypted_token == "SECRET_FOR_TEST'; DROP TABLE USERS; --"
      security_concern = "sql_injection"
    }

    xss = {
      input = pyvider_private_state_verifier.xss_test.input_value
      output = pyvider_private_state_verifier.xss_test.decrypted_token
      expected = "SECRET_FOR_<SCRIPT>ALERT('XSS')</SCRIPT>"
      passed = pyvider_private_state_verifier.xss_test.decrypted_token == "SECRET_FOR_<SCRIPT>ALERT('XSS')</SCRIPT>"
      security_concern = "xss_injection"
    }

    path_traversal = {
      input = pyvider_private_state_verifier.path_traversal_test.input_value
      output = pyvider_private_state_verifier.path_traversal_test.decrypted_token
      expected = "SECRET_FOR_../../../ETC/PASSWD"
      passed = pyvider_private_state_verifier.path_traversal_test.decrypted_token == "SECRET_FOR_../../../ETC/PASSWD"
      security_concern = "path_traversal"
    }

    command_injection = {
      input = pyvider_private_state_verifier.command_injection_test.input_value
      output = pyvider_private_state_verifier.command_injection_test.decrypted_token
      expected = "SECRET_FOR_TEST; CAT /ETC/PASSWD"
      passed = pyvider_private_state_verifier.command_injection_test.decrypted_token == "SECRET_FOR_TEST; CAT /ETC/PASSWD"
      security_concern = "command_injection"
    }

    buffer_overflow = {
      input = substr(pyvider_private_state_verifier.buffer_overflow_test.input_value, 0, 50) # Show first 50 chars
      output = substr(pyvider_private_state_verifier.buffer_overflow_test.decrypted_token, 0, 50) # Show first 50 chars
      expected = "SECRET_FOR_" + join("", [for i in range(1000) : "A"])
      passed = pyvider_private_state_verifier.buffer_overflow_test.decrypted_token == ("SECRET_FOR_" + join("", [for i in range(1000) : "A"]))
      security_concern = "buffer_overflow"
      full_length = length(pyvider_private_state_verifier.buffer_overflow_test.decrypted_token)
    }

    empty_input = {
      input = pyvider_private_state_verifier.empty_test.input_value
      output = pyvider_private_state_verifier.empty_test.decrypted_token
      expected = "SECRET_FOR_"
      passed = pyvider_private_state_verifier.empty_test.decrypted_token == "SECRET_FOR_"
      security_concern = "empty_input"
    }

    whitespace = {
      input = pyvider_private_state_verifier.whitespace_test.input_value
      output = pyvider_private_state_verifier.whitespace_test.decrypted_token
      expected = "SECRET_FOR_   SPACES   AND   TABS	"
      passed = pyvider_private_state_verifier.whitespace_test.decrypted_token == "SECRET_FOR_   SPACES   AND   TABS	"
      security_concern = "whitespace_handling"
    }

    binary_like = {
      input = pyvider_private_state_verifier.binary_test.input_value
      output = pyvider_private_state_verifier.binary_test.decrypted_token
      expected = "SECRET_FOR_BINARY-001101001100001"
      passed = pyvider_private_state_verifier.binary_test.decrypted_token == "SECRET_FOR_BINARY-001101001100001"
      security_concern = "binary_data"
    }

    json_like = {
      input = pyvider_private_state_verifier.json_test.input_value
      output = pyvider_private_state_verifier.json_test.decrypted_token
      expected = "SECRET_FOR_{\"MALICIOUS\":\"PAYLOAD\"}"
      passed = pyvider_private_state_verifier.json_test.decrypted_token == "SECRET_FOR_{\"MALICIOUS\":\"PAYLOAD\"}"
      security_concern = "json_injection"
    }
  }

  security_summary = {
    total_tests = length(local.security_tests)
    passed_tests = length([for test in local.security_tests : test if test.passed])
    failed_tests = length([for test in local.security_tests : test if !test.passed])
    all_tests_passed = alltrue([for test in local.security_tests : test.passed])

    failed_test_names = [
      for test_name, test in local.security_tests : test_name
      if !test.passed
    ]

    security_concerns_tested = [
      for test in local.security_tests : test.security_concern
    ]
  }

  # Detailed security analysis
  security_analysis = {
    encryption_resilience = local.security_summary.all_tests_passed
    input_sanitization = "not_applicable" # Raw input is preserved
    injection_resistance = local.security_summary.all_tests_passed
    buffer_handling = local.security_tests.buffer_overflow.passed
    unicode_support = local.security_tests.unicode.passed
    edge_case_handling = (
      local.security_tests.empty_input.passed &&
      local.security_tests.whitespace.passed
    )
  }
}

# Create comprehensive security report
resource "pyvider_file_content" "security_report" {
  filename = "/tmp/private_state_security_report.json"
  content = jsonencode({
    timestamp = timestamp()
    test_type = "security_verification"

    executive_summary = {
      total_security_tests = local.security_summary.total_tests
      passed_tests = local.security_summary.passed_tests
      failed_tests = local.security_summary.failed_tests
      overall_security_status = local.security_summary.all_tests_passed ? "secure" : "needs_review"
      risk_level = local.security_summary.all_tests_passed ? "low" : "medium"
    }

    test_results = local.security_tests

    security_analysis = local.security_analysis

    threat_vectors_tested = [
      {
        threat = "SQL Injection"
        test_name = "sql_injection"
        status = local.security_tests.sql_injection.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of SQL injection attempts in input"
      },
      {
        threat = "Cross-Site Scripting (XSS)"
        test_name = "xss"
        status = local.security_tests.xss.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of XSS payload in input"
      },
      {
        threat = "Path Traversal"
        test_name = "path_traversal"
        status = local.security_tests.path_traversal.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of path traversal attempts"
      },
      {
        threat = "Command Injection"
        test_name = "command_injection"
        status = local.security_tests.command_injection.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of command injection attempts"
      },
      {
        threat = "Buffer Overflow"
        test_name = "buffer_overflow"
        status = local.security_tests.buffer_overflow.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of extremely long input values"
      }
    ]

    compliance_checks = {
      input_validation = "raw_input_preserved"
      output_transformation = "uppercase_conversion"
      encryption_strength = "terraform_native"
      state_protection = "private_state_encrypted"
      data_integrity = local.security_summary.all_tests_passed ? "verified" : "compromised"
    }

    recommendations = concat(
      local.security_summary.all_tests_passed ? [
        "✅ All security tests passed",
        "✅ Private state encryption is working correctly",
        "✅ Input handling is robust across threat vectors"
      ] : [
        "⚠️ Some security tests failed",
        "⚠️ Review failed tests for potential vulnerabilities"
      ],
      [
        "🔒 Continue using private state for sensitive data",
        "📋 Regularly test with various input types",
        "🛡️ Monitor for new threat vectors",
        "📊 Include security testing in CI/CD pipeline"
      ]
    )
  })
}

# Create detailed security analysis
resource "pyvider_file_content" "security_analysis" {
  filename = "/tmp/security_analysis_detailed.txt"
  content = join("\n", [
    "=== Comprehensive Security Analysis ===",
    "",
    "Test Date: ${timestamp()}",
    "Test Type: Private State Encryption Security Verification",
    "Total Tests: ${local.security_summary.total_tests}",
    "Passed: ${local.security_summary.passed_tests}",
    "Failed: ${local.security_summary.failed_tests}",
    "Overall Status: ${local.security_summary.all_tests_passed ? "✅ SECURE" : "⚠️ NEEDS REVIEW"}",
    "",
    "=== Threat Vector Analysis ===",
    "",
    "1. Unicode/Internationalization Attack:",
    "   Input: 'unicode-тест-测试-テスト'",
    "   Result: ${local.security_tests.unicode.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Unicode injection, encoding attacks",
    "   Mitigation: Input preserved, uppercase transformation applied",
    "",
    "2. Special Characters Injection:",
    "   Input: 'symbols!@#$%^&*()_+-=[]{}|;:,.<>?'",
    "   Result: ${local.security_tests.symbols.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Symbol-based injection attacks",
    "   Mitigation: All symbols preserved and processed correctly",
    "",
    "3. SQL Injection Attempt:",
    "   Input: 'test'; DROP TABLE users; --'",
    "   Result: ${local.security_tests.sql_injection.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Database compromise",
    "   Mitigation: Input treated as literal string, no SQL execution",
    "",
    "4. Cross-Site Scripting (XSS):",
    "   Input: '<script>alert('xss')</script>'",
    "   Result: ${local.security_tests.xss.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Client-side code execution",
    "   Mitigation: HTML tags preserved as literal text",
    "",
    "5. Path Traversal Attack:",
    "   Input: '../../../etc/passwd'",
    "   Result: ${local.security_tests.path_traversal.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Unauthorized file system access",
    "   Mitigation: Path components treated as literal string",
    "",
    "6. Command Injection:",
    "   Input: 'test; cat /etc/passwd'",
    "   Result: ${local.security_tests.command_injection.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: System command execution",
    "   Mitigation: Command syntax preserved as literal text",
    "",
    "7. Buffer Overflow Simulation:",
    "   Input: ${local.security_tests.buffer_overflow.full_length} character string",
    "   Result: ${local.security_tests.buffer_overflow.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Memory corruption, system crash",
    "   Mitigation: Large inputs handled correctly",
    "",
    "8. Empty Input Edge Case:",
    "   Input: ''",
    "   Result: ${local.security_tests.empty_input.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Null pointer, undefined behavior",
    "   Mitigation: Empty input processed correctly",
    "",
    "9. Whitespace Handling:",
    "   Input: '   spaces   and   tabs	'",
    "   Result: ${local.security_tests.whitespace.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Whitespace-based attacks",
    "   Mitigation: Whitespace preserved correctly",
    "",
    "10. Binary Data Simulation:",
    "    Input: 'binary-001101001100001'",
    "    Result: ${local.security_tests.binary_like.passed ? "✅ PASSED" : "❌ FAILED"}",
    "    Risk: Binary data injection",
    "    Mitigation: Binary-like data handled as text",
    "",
    "11. JSON Injection:",
    "    Input: '{\"malicious\":\"payload\"}'",
    "    Result: ${local.security_tests.json_like.passed ? "✅ PASSED" : "❌ FAILED"}",
    "    Risk: JSON structure manipulation",
    "    Mitigation: JSON treated as literal string",
    "",
    "=== Security Assessment ===",
    "",
    "Encryption Resilience: ${local.security_analysis.encryption_resilience ? "✅ ROBUST" : "⚠️ WEAK"}",
    "Input Sanitization: ${local.security_analysis.input_sanitization} (Raw preservation)",
    "Injection Resistance: ${local.security_analysis.injection_resistance ? "✅ STRONG" : "⚠️ VULNERABLE"}",
    "Buffer Handling: ${local.security_analysis.buffer_handling ? "✅ SECURE" : "⚠️ VULNERABLE"}",
    "Unicode Support: ${local.security_analysis.unicode_support ? "✅ CORRECT" : "⚠️ BROKEN"}",
    "Edge Case Handling: ${local.security_analysis.edge_case_handling ? "✅ ROBUST" : "⚠️ FRAGILE"}",
    "",
    "=== Key Security Findings ===",
    "",
    "✅ Private state encryption prevents sensitive data exposure",
    "✅ Input transformation (uppercase) is applied consistently",
    "✅ No code execution occurs from malicious input",
    "✅ Large inputs are handled without buffer overflow",
    "✅ Special characters and unicode are preserved correctly",
    "✅ Edge cases (empty, whitespace) are handled properly",
    "",
    "=== Threat Mitigation Summary ===",
    "",
    "The private state verifier demonstrates robust security characteristics:",
    "• Input is treated as literal data, preventing injection attacks",
    "• Terraform's encryption mechanisms protect sensitive data at rest",
    "• No dynamic code execution based on input content",
    "• Consistent uppercase transformation applied to all input",
    "• Unicode and special characters handled correctly",
    "• Buffer overflow protection through proper string handling",
    "",
    length(local.security_summary.failed_test_names) > 0 ? "=== Failed Tests Requiring Review ===" : "",
    length(local.security_summary.failed_test_names) > 0 ? join("\n", [for test in local.security_summary.failed_test_names : "❌ ${test}"]) : "",
    "",
    "=== Recommendations ===",
    "",
    local.security_summary.all_tests_passed ? "🎉 All security tests passed! The implementation is secure." : "⚠️ Review failed tests and address security concerns.",
    "🔒 Continue using private state for sensitive data storage",
    "📋 Include these security tests in automated CI/CD pipelines",
    "🛡️ Monitor for new attack vectors and update tests accordingly",
    "📊 Regular security audits recommended",
    "",
    "Report Generated: ${timestamp()}",
    "Next Review: Recommended within 90 days"
  ])
}

# Create SAST/Security scan summary for CI/CD
resource "pyvider_file_content" "sast_summary" {
  filename = "/tmp/sast_security_summary.json"
  content = jsonencode({
    scan_info = {
      timestamp = timestamp()
      scan_type = "static_analysis_security_testing"
      tool = "pyvider_private_state_verifier"
      version = "1.0"
    }

    summary = {
      total_vulnerabilities = local.security_summary.failed_tests
      critical = 0
      high = local.security_summary.failed_tests
      medium = 0
      low = 0
      info = local.security_summary.passed_tests
    }

    findings = [
      for test_name, test in local.security_tests : {
        id = "PSV-${upper(substr(test_name, 0, 3))}-001"
        title = "Private State ${title(replace(test.security_concern, "_", " "))} Test"
        severity = test.passed ? "info" : "high"
        status = test.passed ? "passed" : "failed"
        category = "encryption_verification"
        description = "Testing private state encryption with ${test.security_concern} input vector"
        recommendation = test.passed ? "No action required" : "Review encryption handling for this input type"
        test_vector = test.input
        expected_output = test.expected
        actual_output = test.output
      }
    ]

    compliance = {
      owasp_top_10 = {
        injection = local.security_tests.sql_injection.passed && local.security_tests.command_injection.passed ? "compliant" : "non_compliant"
        xss = local.security_tests.xss.passed ? "compliant" : "non_compliant"
        security_misconfiguration = "not_applicable"
        sensitive_data_exposure = local.security_summary.all_tests_passed ? "compliant" : "non_compliant"
      }

      encryption_standards = {
        data_at_rest = "terraform_managed"
        key_management = "terraform_managed"
        algorithm = "terraform_default"
      }
    }

    exit_code = local.security_summary.all_tests_passed ? 0 : 1
    pass_criteria = "all_tests_must_pass"
  })
}

output "security_testing_results" {
  description = "Comprehensive security testing results for private state encryption"
  value = {
    summary = local.security_summary

    security_status = local.security_summary.all_tests_passed ? "secure" : "needs_review"

    threat_vectors_tested = local.security_summary.security_concerns_tested

    critical_findings = length(local.security_summary.failed_test_names) > 0 ? local.security_summary.failed_test_names : []

    security_analysis = local.security_analysis

    compliance_status = {
      encryption_verified = local.security_summary.all_tests_passed
      injection_resistant = (
        local.security_tests.sql_injection.passed &&
        local.security_tests.command_injection.passed &&
        local.security_tests.xss.passed
      )
      buffer_secure = local.security_tests.buffer_overflow.passed
      unicode_compliant = local.security_tests.unicode.passed
    }

    files_generated = [
      pyvider_file_content.security_report.filename,
      pyvider_file_content.security_analysis.filename,
      pyvider_file_content.sast_summary.filename
    ]
  }
}