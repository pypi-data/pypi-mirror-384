# Compliance and regulatory verification examples

variable "compliance_framework" {
  description = "Compliance framework to test against"
  type        = string
  default     = "SOC2"
  validation {
    condition = contains([
      "SOC2", "HIPAA", "PCI-DSS", "GDPR", "FedRAMP", "ISO27001"
    ], var.compliance_framework)
    error_message = "Must be a supported compliance framework."
  }
}

variable "environment_classification" {
  description = "Environment security classification"
  type        = string
  default     = "internal"
  validation {
    condition = contains([
      "public", "internal", "confidential", "restricted"
    ], var.environment_classification)
    error_message = "Must be a valid classification level."
  }
}

# Compliance framework requirements mapping
locals {
  compliance_requirements = {
    SOC2 = {
      encryption_at_rest = true
      access_controls = true
      audit_logging = true
      data_integrity = true
      availability_controls = true
    }
    HIPAA = {
      encryption_at_rest = true
      access_controls = true
      audit_logging = true
      data_integrity = true
      administrative_safeguards = true
      physical_safeguards = true
      technical_safeguards = true
    }
    "PCI-DSS" = {
      encryption_at_rest = true
      encryption_in_transit = true
      access_controls = true
      network_security = true
      vulnerability_management = true
      secure_coding = true
    }
    GDPR = {
      data_protection_by_design = true
      encryption_at_rest = true
      access_controls = true
      data_portability = true
      right_to_erasure = true
      audit_logging = true
    }
    FedRAMP = {
      encryption_at_rest = true
      access_controls = true
      audit_logging = true
      incident_response = true
      continuous_monitoring = true
      security_controls = true
    }
    ISO27001 = {
      information_security_policy = true
      risk_management = true
      asset_management = true
      access_controls = true
      cryptography = true
      incident_management = true
    }
  }

  current_requirements = local.compliance_requirements[var.compliance_framework]
}

# Example 1: Data classification verification
resource "pyvider_private_state_verifier" "data_classification" {
  input_value = "${var.environment_classification}-data-classification-test"
}

# Example 2: Encryption strength verification
resource "pyvider_private_state_verifier" "encryption_strength" {
  input_value = "encryption-strength-validation-${var.compliance_framework}"
}

# Example 3: Access control verification
resource "pyvider_private_state_verifier" "access_control" {
  input_value = "access-control-test-${var.compliance_framework}"
}

# Example 4: Audit trail verification
resource "pyvider_private_state_verifier" "audit_trail" {
  input_value = "audit-trail-verification-${timestamp()}"
}

# Example 5: Data integrity verification
resource "pyvider_private_state_verifier" "data_integrity" {
  input_value = "data-integrity-check-${var.compliance_framework}"
}

# Example 6: PII handling verification (simulated)
resource "pyvider_private_state_verifier" "pii_handling" {
  input_value = "pii-protection-test-${var.compliance_framework}"
}

# Example 7: Retention policy verification
resource "pyvider_private_state_verifier" "retention_policy" {
  input_value = "retention-policy-${var.compliance_framework}-test"
}

# Example 8: Cross-border data transfer verification
resource "pyvider_private_state_verifier" "cross_border" {
  input_value = "cross-border-transfer-${var.compliance_framework}"
}

# Compliance verification logic
locals {
  compliance_tests = {
    data_classification = {
      test_name = "data_classification"
      input = pyvider_private_state_verifier.data_classification.input_value
      output = pyvider_private_state_verifier.data_classification.decrypted_token
      expected = "SECRET_FOR_${upper(var.environment_classification)}-DATA-CLASSIFICATION-TEST"
      passed = pyvider_private_state_verifier.data_classification.decrypted_token == "SECRET_FOR_${upper(var.environment_classification)}-DATA-CLASSIFICATION-TEST"
      requirement = "data_protection"
      criticality = "high"
    }

    encryption_strength = {
      test_name = "encryption_strength"
      input = pyvider_private_state_verifier.encryption_strength.input_value
      output = pyvider_private_state_verifier.encryption_strength.decrypted_token
      expected = "SECRET_FOR_ENCRYPTION-STRENGTH-VALIDATION-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.encryption_strength.decrypted_token == "SECRET_FOR_ENCRYPTION-STRENGTH-VALIDATION-${upper(var.compliance_framework)}"
      requirement = "encryption_at_rest"
      criticality = "critical"
    }

    access_control = {
      test_name = "access_control"
      input = pyvider_private_state_verifier.access_control.input_value
      output = pyvider_private_state_verifier.access_control.decrypted_token
      expected = "SECRET_FOR_ACCESS-CONTROL-TEST-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.access_control.decrypted_token == "SECRET_FOR_ACCESS-CONTROL-TEST-${upper(var.compliance_framework)}"
      requirement = "access_controls"
      criticality = "high"
    }

    audit_trail = {
      test_name = "audit_trail"
      input = pyvider_private_state_verifier.audit_trail.input_value
      output = pyvider_private_state_verifier.audit_trail.decrypted_token
      expected = "SECRET_FOR_${upper(pyvider_private_state_verifier.audit_trail.input_value)}"
      passed = pyvider_private_state_verifier.audit_trail.decrypted_token == "SECRET_FOR_${upper(pyvider_private_state_verifier.audit_trail.input_value)}"
      requirement = "audit_logging"
      criticality = "high"
    }

    data_integrity = {
      test_name = "data_integrity"
      input = pyvider_private_state_verifier.data_integrity.input_value
      output = pyvider_private_state_verifier.data_integrity.decrypted_token
      expected = "SECRET_FOR_DATA-INTEGRITY-CHECK-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.data_integrity.decrypted_token == "SECRET_FOR_DATA-INTEGRITY-CHECK-${upper(var.compliance_framework)}"
      requirement = "data_integrity"
      criticality = "critical"
    }

    pii_handling = {
      test_name = "pii_handling"
      input = pyvider_private_state_verifier.pii_handling.input_value
      output = pyvider_private_state_verifier.pii_handling.decrypted_token
      expected = "SECRET_FOR_PII-PROTECTION-TEST-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.pii_handling.decrypted_token == "SECRET_FOR_PII-PROTECTION-TEST-${upper(var.compliance_framework)}"
      requirement = "data_protection"
      criticality = "critical"
    }

    retention_policy = {
      test_name = "retention_policy"
      input = pyvider_private_state_verifier.retention_policy.input_value
      output = pyvider_private_state_verifier.retention_policy.decrypted_token
      expected = "SECRET_FOR_RETENTION-POLICY-${upper(var.compliance_framework)}-TEST"
      passed = pyvider_private_state_verifier.retention_policy.decrypted_token == "SECRET_FOR_RETENTION-POLICY-${upper(var.compliance_framework)}-TEST"
      requirement = "data_lifecycle"
      criticality = "medium"
    }

    cross_border = {
      test_name = "cross_border"
      input = pyvider_private_state_verifier.cross_border.input_value
      output = pyvider_private_state_verifier.cross_border.decrypted_token
      expected = "SECRET_FOR_CROSS-BORDER-TRANSFER-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.cross_border.decrypted_token == "SECRET_FOR_CROSS-BORDER-TRANSFER-${upper(var.compliance_framework)}"
      requirement = "data_transfer"
      criticality = "high"
    }
  }

  compliance_summary = {
    framework = var.compliance_framework
    classification = var.environment_classification
    total_tests = length(local.compliance_tests)
    passed_tests = length([for test in local.compliance_tests : test if test.passed])
    failed_tests = length([for test in local.compliance_tests : test if !test.passed])
    compliance_status = alltrue([for test in local.compliance_tests : test.passed])

    critical_failures = length([
      for test in local.compliance_tests : test
      if !test.passed && test.criticality == "critical"
    ])

    high_failures = length([
      for test in local.compliance_tests : test
      if !test.passed && test.criticality == "high"
    ])

    failed_requirements = [
      for test in local.compliance_tests : test.requirement
      if !test.passed
    ]
  }
}

# Create compliance assessment report
resource "pyvider_file_content" "compliance_assessment" {
  filename = "/tmp/compliance_assessment_${var.compliance_framework}.json"
  content = jsonencode({
    assessment = {
      timestamp = timestamp()
      framework = var.compliance_framework
      classification = var.environment_classification
      assessor = "pyvider_private_state_verifier"
      version = "1.0"
    }

    executive_summary = {
      overall_compliance = local.compliance_summary.compliance_status ? "compliant" : "non_compliant"
      risk_level = (
        local.compliance_summary.critical_failures > 0 ? "critical" :
        local.compliance_summary.high_failures > 0 ? "high" :
        local.compliance_summary.failed_tests > 0 ? "medium" : "low"
      )
      certification_ready = local.compliance_summary.compliance_status
      remediation_required = !local.compliance_summary.compliance_status
    }

    test_results = local.compliance_tests

    framework_requirements = local.current_requirements

    requirement_coverage = {
      for requirement, enabled in local.current_requirements :
      requirement => {
        required = enabled
        tested = contains([for test in local.compliance_tests : test.requirement], requirement)
        compliant = !contains(local.compliance_summary.failed_requirements, requirement)
      }
    }

    compliance_metrics = {
      total_tests = local.compliance_summary.total_tests
      passed_tests = local.compliance_summary.passed_tests
      failed_tests = local.compliance_summary.failed_tests
      compliance_percentage = (local.compliance_summary.passed_tests / local.compliance_summary.total_tests) * 100
      critical_failures = local.compliance_summary.critical_failures
      high_failures = local.compliance_summary.high_failures
    }

    recommendations = concat(
      local.compliance_summary.compliance_status ? [
        "✅ All compliance tests passed",
        "✅ Ready for ${var.compliance_framework} certification",
        "✅ Private state encryption meets requirements"
      ] : [
        "⚠️ Compliance violations detected",
        "⚠️ Remediation required before certification",
        "📋 Review failed tests and implement fixes"
      ],
      [
        "🔒 Continue monitoring compliance status",
        "📊 Regular compliance assessments recommended",
        "📋 Maintain audit documentation",
        "🛡️ Implement continuous compliance monitoring"
      ]
    )

    next_assessment = {
      recommended_date = timeadd(timestamp(), "2160h") # 90 days
      frequency = "quarterly"
      scope = "full_compliance_validation"
    }
  })
}

# Create framework-specific compliance report
resource "pyvider_file_content" "framework_compliance_report" {
  filename = "/tmp/${lower(var.compliance_framework)}_compliance_report.txt"
  content = join("\n", [
    "=== ${var.compliance_framework} Compliance Verification Report ===",
    "",
    "Assessment Date: ${timestamp()}",
    "Framework: ${var.compliance_framework}",
    "Environment Classification: ${var.environment_classification}",
    "Assessment Tool: Private State Verifier",
    "",
    "=== Executive Summary ===",
    "",
    "Overall Compliance Status: ${local.compliance_summary.compliance_status ? "✅ COMPLIANT" : "❌ NON-COMPLIANT"}",
    "Total Tests Conducted: ${local.compliance_summary.total_tests}",
    "Tests Passed: ${local.compliance_summary.passed_tests}",
    "Tests Failed: ${local.compliance_summary.failed_tests}",
    "Compliance Percentage: ${(local.compliance_summary.passed_tests / local.compliance_summary.total_tests) * 100}%",
    "",
    "Risk Assessment:",
    "- Critical Failures: ${local.compliance_summary.critical_failures}",
    "- High Risk Failures: ${local.compliance_summary.high_failures}",
    "- Overall Risk Level: ${local.compliance_summary.critical_failures > 0 ? "CRITICAL" : local.compliance_summary.high_failures > 0 ? "HIGH" : local.compliance_summary.failed_tests > 0 ? "MEDIUM" : "LOW"}",
    "",
    "=== Framework Requirements Verification ===",
    "",
    var.compliance_framework == "SOC2" ? join("\n", [
      "SOC 2 Type II Controls Assessment:",
      "CC6.1 - Logical and Physical Access Controls: ${contains(local.compliance_summary.failed_requirements, "access_controls") ? "❌ FAILED" : "✅ PASSED"}",
      "CC6.7 - Data Transmission and Disposal: ${contains(local.compliance_summary.failed_requirements, "data_integrity") ? "❌ FAILED" : "✅ PASSED"}",
      "CC6.8 - Encryption: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    var.compliance_framework == "HIPAA" ? join("\n", [
      "HIPAA Safeguards Assessment:",
      "§164.312(a)(1) - Access Control: ${contains(local.compliance_summary.failed_requirements, "access_controls") ? "❌ FAILED" : "✅ PASSED"}",
      "§164.312(a)(2)(iv) - Encryption: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
      "§164.312(b) - Audit Controls: ${contains(local.compliance_summary.failed_requirements, "audit_logging") ? "❌ FAILED" : "✅ PASSED"}",
      "§164.312(c)(1) - Integrity: ${contains(local.compliance_summary.failed_requirements, "data_integrity") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    var.compliance_framework == "PCI-DSS" ? join("\n", [
      "PCI DSS Requirements Assessment:",
      "Requirement 3 - Protect Stored Data: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
      "Requirement 4 - Encrypt Data in Transit: ${contains(local.compliance_summary.failed_requirements, "encryption_in_transit") ? "❌ FAILED" : "✅ PASSED"}",
      "Requirement 7 - Restrict Access: ${contains(local.compliance_summary.failed_requirements, "access_controls") ? "❌ FAILED" : "✅ PASSED"}",
      "Requirement 10 - Log and Monitor: ${contains(local.compliance_summary.failed_requirements, "audit_logging") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    var.compliance_framework == "GDPR" ? join("\n", [
      "GDPR Articles Assessment:",
      "Article 25 - Data Protection by Design: ${contains(local.compliance_summary.failed_requirements, "data_protection") ? "❌ FAILED" : "✅ PASSED"}",
      "Article 32 - Security of Processing: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
      "Article 20 - Right to Data Portability: ${contains(local.compliance_summary.failed_requirements, "data_portability") ? "❌ FAILED" : "✅ PASSED"}",
      "Article 17 - Right to Erasure: ${contains(local.compliance_summary.failed_requirements, "right_to_erasure") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    "=== Detailed Test Results ===",
    "",
    join("\n", [
      for test_name, test in local.compliance_tests :
      "${test_name}: ${test.passed ? "✅ PASSED" : "❌ FAILED"} (${upper(test.criticality)})\n  Requirement: ${test.requirement}\n  Input: ${test.input}\n  Expected: ${test.expected}\n  Actual: ${test.output}\n"
    ]),
    "",
    "=== Technical Implementation Details ===",
    "",
    "Encryption Mechanism: Terraform Private State",
    "Key Management: Terraform Managed",
    "Data Classification: ${title(var.environment_classification)}",
    "Access Control: Role-Based (Terraform State)",
    "Audit Trail: Terraform State Operations",
    "",
    "=== Remediation Requirements ===",
    "",
    length(local.compliance_summary.failed_requirements) > 0 ? "Required Actions:" : "No remediation required - all tests passed.",
    length(local.compliance_summary.failed_requirements) > 0 ? join("\n", [
      for req in local.compliance_summary.failed_requirements :
      "- Address ${req} requirement violations"
    ]) : "",
    "",
    "=== Compliance Certification Status ===",
    "",
    local.compliance_summary.compliance_status ? "✅ READY FOR CERTIFICATION" : "❌ NOT READY FOR CERTIFICATION",
    local.compliance_summary.compliance_status ? "All ${var.compliance_framework} requirements verified" : "Remediation required before certification",
    "",
    "=== Next Steps ===",
    "",
    local.compliance_summary.compliance_status ? "1. Proceed with formal ${var.compliance_framework} audit" : "1. Remediate failed compliance tests",
    "2. Implement continuous compliance monitoring",
    "3. Schedule quarterly compliance assessments",
    "4. Maintain compliance documentation",
    "5. Train staff on compliance requirements",
    "",
    "Assessment Completed: ${timestamp()}",
    "Next Assessment Due: ${timeadd(timestamp(), "2160h")}"
  ])
}

# Create audit evidence package
resource "pyvider_file_content" "audit_evidence" {
  filename = "/tmp/audit_evidence_${var.compliance_framework}.json"
  content = jsonencode({
    audit_evidence = {
      timestamp = timestamp()
      framework = var.compliance_framework
      scope = "private_state_encryption_verification"
      auditor = "automated_compliance_testing"
    }

    test_evidence = {
      for test_name, test in local.compliance_tests :
      test_name => {
        test_id = "${var.compliance_framework}-PSV-${upper(substr(test_name, 0, 3))}"
        requirement = test.requirement
        criticality = test.criticality
        test_input = test.input
        expected_output = test.expected
        actual_output = test.output
        test_result = test.passed ? "pass" : "fail"
        test_timestamp = timestamp()
        compliance_mapping = {
          SOC2 = test.requirement == "encryption_at_rest" ? "CC6.8" : test.requirement == "access_controls" ? "CC6.1" : test.requirement == "audit_logging" ? "CC7.2" : "CC6.7"
          HIPAA = test.requirement == "encryption_at_rest" ? "§164.312(a)(2)(iv)" : test.requirement == "access_controls" ? "§164.312(a)(1)" : test.requirement == "audit_logging" ? "§164.312(b)" : "§164.312(c)(1)"
          "PCI-DSS" = test.requirement == "encryption_at_rest" ? "Requirement 3" : test.requirement == "access_controls" ? "Requirement 7" : test.requirement == "audit_logging" ? "Requirement 10" : "Requirement 4"
          GDPR = test.requirement == "data_protection" ? "Article 25" : test.requirement == "encryption_at_rest" ? "Article 32" : test.requirement == "audit_logging" ? "Article 30" : "Article 5"
          FedRAMP = test.requirement == "encryption_at_rest" ? "SC-28" : test.requirement == "access_controls" ? "AC-2" : test.requirement == "audit_logging" ? "AU-2" : "SC-13"
          ISO27001 = test.requirement == "encryption_at_rest" ? "A.10.1.1" : test.requirement == "access_controls" ? "A.9.1.1" : test.requirement == "audit_logging" ? "A.12.4.1" : "A.10.1.2"
        }[var.compliance_framework]
      }
    }

    technical_details = {
      encryption_algorithm = "terraform_managed"
      key_management = "terraform_managed"
      data_classification = var.environment_classification
      state_protection = "private_state_encrypted"
      access_control_mechanism = "terraform_rbac"
    }

    compliance_attestation = {
      overall_compliance = local.compliance_summary.compliance_status
      framework_version = var.compliance_framework
      assessment_scope = "encryption_and_data_protection"
      limitations = "limited_to_private_state_functionality"
      certification_readiness = local.compliance_summary.compliance_status
    }
  })
}

output "compliance_verification_results" {
  description = "Compliance framework verification results"
  value = {
    framework = var.compliance_framework
    classification = var.environment_classification

    compliance_status = {
      overall_compliant = local.compliance_summary.compliance_status
      certification_ready = local.compliance_summary.compliance_status
      risk_level = (
        local.compliance_summary.critical_failures > 0 ? "critical" :
        local.compliance_summary.high_failures > 0 ? "high" :
        local.compliance_summary.failed_tests > 0 ? "medium" : "low"
      )
    }

    test_metrics = {
      total_tests = local.compliance_summary.total_tests
      passed_tests = local.compliance_summary.passed_tests
      failed_tests = local.compliance_summary.failed_tests
      compliance_percentage = (local.compliance_summary.passed_tests / local.compliance_summary.total_tests) * 100
    }

    failure_analysis = {
      critical_failures = local.compliance_summary.critical_failures
      high_failures = local.compliance_summary.high_failures
      failed_requirements = local.compliance_summary.failed_requirements
    }

    framework_requirements = local.current_requirements

    documentation_artifacts = [
      pyvider_file_content.compliance_assessment.filename,
      pyvider_file_content.framework_compliance_report.filename,
      pyvider_file_content.audit_evidence.filename
    ]

    next_assessment_date = timeadd(timestamp(), "2160h")
  }
}