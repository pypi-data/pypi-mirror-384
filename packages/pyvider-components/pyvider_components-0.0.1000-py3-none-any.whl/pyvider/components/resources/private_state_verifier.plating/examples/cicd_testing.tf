# CI/CD pipeline integration examples for private state verification

variable "ci_environment" {
  description = "CI/CD environment identifier"
  type        = string
  default     = "ci-test"
}

variable "build_number" {
  description = "Build number or identifier"
  type        = string
  default     = "local-build"
}

variable "test_suite" {
  description = "Test suite configuration"
  type = object({
    name = string
    parallel_tests = bool
    timeout_minutes = number
    failure_threshold = number
  })
  default = {
    name = "private-state-verification"
    parallel_tests = true
    timeout_minutes = 10
    failure_threshold = 0
  }
}

# CI/CD test matrix - multiple test scenarios
locals {
  ci_test_matrix = {
    smoke_test = {
      input = "ci-smoke-test-${var.build_number}"
      description = "Basic functionality verification"
      priority = "critical"
      timeout = 60
    }
    integration_test = {
      input = "ci-integration-${var.ci_environment}-${var.build_number}"
      description = "Integration testing with CI environment"
      priority = "high"
      timeout = 120
    }
    regression_test = {
      input = "ci-regression-validation-${var.build_number}"
      description = "Regression testing for known issues"
      priority = "high"
      timeout = 180
    }
    performance_test = {
      input = "ci-performance-benchmark-${var.build_number}"
      description = "Performance and scalability verification"
      priority = "medium"
      timeout = 300
    }
    security_test = {
      input = "ci-security-scan-${var.build_number}"
      description = "Security vulnerability assessment"
      priority = "critical"
      timeout = 240
    }
    compatibility_test = {
      input = "ci-compatibility-${var.ci_environment}"
      description = "Environment compatibility verification"
      priority = "medium"
      timeout = 150
    }
  }
}

# Create test instances for each test in the matrix
resource "pyvider_private_state_verifier" "ci_test_matrix" {
  for_each = local.ci_test_matrix

  input_value = each.value.input
}

# Example 1: GitHub Actions CI/CD integration
resource "pyvider_private_state_verifier" "github_actions_test" {
  input_value = "github-actions-${var.ci_environment}-${var.build_number}"
}

# Example 2: Jenkins pipeline integration
resource "pyvider_private_state_verifier" "jenkins_test" {
  input_value = "jenkins-pipeline-${var.ci_environment}-${var.build_number}"
}

# Example 3: GitLab CI integration
resource "pyvider_private_state_verifier" "gitlab_ci_test" {
  input_value = "gitlab-ci-${var.ci_environment}-${var.build_number}"
}

# Example 4: Azure DevOps integration
resource "pyvider_private_state_verifier" "azure_devops_test" {
  input_value = "azure-devops-${var.ci_environment}-${var.build_number}"
}

# Example 5: CircleCI integration
resource "pyvider_private_state_verifier" "circleci_test" {
  input_value = "circleci-${var.ci_environment}-${var.build_number}"
}

# Test results validation
locals {
  ci_test_results = {
    for test_name, test_config in local.ci_test_matrix :
    test_name => {
      input = pyvider_private_state_verifier.ci_test_matrix[test_name].input_value
      output = pyvider_private_state_verifier.ci_test_matrix[test_name].decrypted_token
      expected = "SECRET_FOR_${upper(test_config.input)}"
      passed = pyvider_private_state_verifier.ci_test_matrix[test_name].decrypted_token == "SECRET_FOR_${upper(test_config.input)}"
      description = test_config.description
      priority = test_config.priority
      timeout = test_config.timeout
      duration = 1 # Simulated test duration in seconds
    }
  }

  platform_test_results = {
    github_actions = {
      input = pyvider_private_state_verifier.github_actions_test.input_value
      output = pyvider_private_state_verifier.github_actions_test.decrypted_token
      expected = "SECRET_FOR_GITHUB-ACTIONS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.github_actions_test.decrypted_token == "SECRET_FOR_GITHUB-ACTIONS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "GitHub Actions"
    }
    jenkins = {
      input = pyvider_private_state_verifier.jenkins_test.input_value
      output = pyvider_private_state_verifier.jenkins_test.decrypted_token
      expected = "SECRET_FOR_JENKINS-PIPELINE-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.jenkins_test.decrypted_token == "SECRET_FOR_JENKINS-PIPELINE-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "Jenkins"
    }
    gitlab_ci = {
      input = pyvider_private_state_verifier.gitlab_ci_test.input_value
      output = pyvider_private_state_verifier.gitlab_ci_test.decrypted_token
      expected = "SECRET_FOR_GITLAB-CI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.gitlab_ci_test.decrypted_token == "SECRET_FOR_GITLAB-CI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "GitLab CI"
    }
    azure_devops = {
      input = pyvider_private_state_verifier.azure_devops_test.input_value
      output = pyvider_private_state_verifier.azure_devops_test.decrypted_token
      expected = "SECRET_FOR_AZURE-DEVOPS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.azure_devops_test.decrypted_token == "SECRET_FOR_AZURE-DEVOPS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "Azure DevOps"
    }
    circleci = {
      input = pyvider_private_state_verifier.circleci_test.input_value
      output = pyvider_private_state_verifier.circleci_test.decrypted_token
      expected = "SECRET_FOR_CIRCLECI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.circleci_test.decrypted_token == "SECRET_FOR_CIRCLECI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "CircleCI"
    }
  }

  # Overall CI/CD test summary
  ci_summary = {
    total_matrix_tests = length(local.ci_test_results)
    matrix_tests_passed = length([for test in local.ci_test_results : test if test.passed])
    matrix_tests_failed = length([for test in local.ci_test_results : test if !test.passed])

    total_platform_tests = length(local.platform_test_results)
    platform_tests_passed = length([for test in local.platform_test_results : test if test.passed])
    platform_tests_failed = length([for test in local.platform_test_results : test if !test.passed])

    overall_tests_passed = (
      length([for test in local.ci_test_results : test if test.passed]) +
      length([for test in local.platform_test_results : test if test.passed])
    )
    overall_tests_failed = (
      length([for test in local.ci_test_results : test if !test.passed]) +
      length([for test in local.platform_test_results : test if !test.passed])
    )

    critical_failures = length([
      for test in local.ci_test_results : test
      if !test.passed && test.priority == "critical"
    ])

    all_tests_passed = (
      alltrue([for test in local.ci_test_results : test.passed]) &&
      alltrue([for test in local.platform_test_results : test.passed])
    )

    ci_status = (
      alltrue([for test in local.ci_test_results : test.passed]) &&
      alltrue([for test in local.platform_test_results : test.passed])
    ) ? "success" : "failure"

    exit_code = (
      alltrue([for test in local.ci_test_results : test.passed]) &&
      alltrue([for test in local.platform_test_results : test.passed])
    ) ? 0 : 1
  }
}

# Create CI/CD test report in JUnit XML format
resource "pyvider_file_content" "junit_test_report" {
  filename = "/tmp/private_state_junit_report.xml"
  content = join("\n", [
    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
    "<testsuites name=\"PrivateStateVerification\" tests=\"${local.ci_summary.overall_tests_passed + local.ci_summary.overall_tests_failed}\" failures=\"${local.ci_summary.overall_tests_failed}\" time=\"${sum([for test in local.ci_test_results : test.duration])}\" timestamp=\"${timestamp()}\">",
    "  <testsuite name=\"MatrixTests\" tests=\"${local.ci_summary.total_matrix_tests}\" failures=\"${local.ci_summary.matrix_tests_failed}\" time=\"${sum([for test in local.ci_test_results : test.duration])}\">",
    join("\n", [
      for test_name, test in local.ci_test_results :
      test.passed ?
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.MatrixTests\" time=\"${test.duration}\" />" :
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.MatrixTests\" time=\"${test.duration}\">\n      <failure message=\"Expected '${test.expected}' but got '${test.output}'\" type=\"AssertionError\">\n        Test: ${test.description}\n        Priority: ${test.priority}\n        Input: ${test.input}\n        Expected: ${test.expected}\n        Actual: ${test.output}\n      </failure>\n    </testcase>"
    ]),
    "  </testsuite>",
    "  <testsuite name=\"PlatformTests\" tests=\"${local.ci_summary.total_platform_tests}\" failures=\"${local.ci_summary.platform_tests_failed}\" time=\"${local.ci_summary.total_platform_tests}\">",
    join("\n", [
      for test_name, test in local.platform_test_results :
      test.passed ?
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.PlatformTests\" time=\"1\" />" :
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.PlatformTests\" time=\"1\">\n      <failure message=\"Expected '${test.expected}' but got '${test.output}'\" type=\"AssertionError\">\n        Platform: ${test.platform}\n        Input: ${test.input}\n        Expected: ${test.expected}\n        Actual: ${test.output}\n      </failure>\n    </testcase>"
    ]),
    "  </testsuite>",
    "</testsuites>"
  ])
}

# Create CI/CD pipeline configuration files
resource "pyvider_file_content" "github_actions_workflow" {
  filename = "/tmp/github_actions_private_state_test.yml"
  content = yamlencode({
    name = "Private State Verification"
    on = {
      push = {
        branches = ["main", "develop"]
      }
      pull_request = {
        branches = ["main"]
      }
    }

    jobs = {
      private_state_test = {
        "runs-on" = "ubuntu-latest"
        steps = [
          {
            name = "Checkout"
            uses = "actions/checkout@v3"
          },
          {
            name = "Setup Terraform"
            uses = "hashicorp/setup-terraform@v2"
            with = {
              terraform_version = "1.5.0"
            }
          },
          {
            name = "Initialize Terraform"
            run = "terraform init"
          },
          {
            name = "Run Private State Tests"
            run = join("\n", [
              "terraform plan -var=\"ci_environment=github-actions\" -var=\"build_number=${{ github.run_number }}\"",
              "terraform apply -auto-approve -var=\"ci_environment=github-actions\" -var=\"build_number=${{ github.run_number }}\"",
            ])
            env = {
              TF_LOG = "INFO"
            }
          },
          {
            name = "Validate Test Results"
            run = join("\n", [
              "if [ \"${local.ci_summary.ci_status}\" = \"success\" ]; then",
              "  echo \"✅ All private state tests passed\"",
              "  exit 0",
              "else",
              "  echo \"❌ Private state tests failed\"",
              "  echo \"Critical failures: ${local.ci_summary.critical_failures}\"",
              "  exit 1",
              "fi"
            ])
          }
        ]
      }
    }
  })
}

# Create Jenkins pipeline configuration
resource "pyvider_file_content" "jenkins_pipeline" {
  filename = "/tmp/Jenkinsfile.private_state_test"
  content = join("\n", [
    "pipeline {",
    "    agent any",
    "    ",
    "    environment {",
    "        CI_ENVIRONMENT = '${var.ci_environment}'",
    "        BUILD_NUMBER = '${var.build_number}'",
    "        TF_LOG = 'INFO'",
    "    }",
    "    ",
    "    stages {",
    "        stage('Initialize') {",
    "            steps {",
    "                echo 'Initializing Private State Verification Tests'",
    "                sh 'terraform init'",
    "            }",
    "        }",
    "        ",
    "        stage('Plan Tests') {",
    "            steps {",
    "                echo 'Planning private state verification tests'",
    "                sh 'terraform plan -var=\"ci_environment=jenkins\" -var=\"build_number=${BUILD_NUMBER}\"'",
    "            }",
    "        }",
    "        ",
    "        stage('Execute Tests') {",
    "            steps {",
    "                echo 'Executing private state verification tests'",
    "                sh 'terraform apply -auto-approve -var=\"ci_environment=jenkins\" -var=\"build_number=${BUILD_NUMBER}\"'",
    "            }",
    "        }",
    "        ",
    "        stage('Validate Results') {",
    "            steps {",
    "                script {",
    "                    if ('${local.ci_summary.ci_status}' == 'success') {",
    "                        echo '✅ All private state tests passed'",
    "                        currentBuild.result = 'SUCCESS'",
    "                    } else {",
    "                        echo '❌ Private state tests failed'",
    "                        echo 'Critical failures: ${local.ci_summary.critical_failures}'",
    "                        currentBuild.result = 'FAILURE'",
    "                        error('Private state verification tests failed')",
    "                    }",
    "                }",
    "            }",
    "        }",
    "    }",
    "    ",
    "    post {",
    "        always {",
    "            echo 'Cleaning up test resources'",
    "            sh 'terraform destroy -auto-approve -var=\"ci_environment=jenkins\" -var=\"build_number=${BUILD_NUMBER}\" || true'",
    "        }",
    "        success {",
    "            echo 'Private state verification completed successfully'",
    "        }",
    "        failure {",
    "            echo 'Private state verification failed - check logs for details'",
    "        }",
    "    }",
    "}"
  ])
}

# Create comprehensive CI/CD test report
resource "pyvider_file_content" "cicd_test_report" {
  filename = "/tmp/cicd_private_state_test_report.json"
  content = jsonencode({
    test_execution = {
      timestamp = timestamp()
      ci_environment = var.ci_environment
      build_number = var.build_number
      test_suite = var.test_suite
      duration_seconds = sum([for test in local.ci_test_results : test.duration])
    }

    test_matrix_results = local.ci_test_results
    platform_test_results = local.platform_test_results

    summary = local.ci_summary

    test_categories = {
      critical_tests = {
        total = length([for test in local.ci_test_results : test if test.priority == "critical"])
        passed = length([for test in local.ci_test_results : test if test.priority == "critical" && test.passed])
        failed = length([for test in local.ci_test_results : test if test.priority == "critical" && !test.passed])
      }
      high_priority_tests = {
        total = length([for test in local.ci_test_results : test if test.priority == "high"])
        passed = length([for test in local.ci_test_results : test if test.priority == "high" && test.passed])
        failed = length([for test in local.ci_test_results : test if test.priority == "high" && !test.passed])
      }
      medium_priority_tests = {
        total = length([for test in local.ci_test_results : test if test.priority == "medium"])
        passed = length([for test in local.ci_test_results : test if test.priority == "medium" && test.passed])
        failed = length([for test in local.ci_test_results : test if test.priority == "medium" && !test.passed])
      }
    }

    platform_compatibility = {
      for platform_name, result in local.platform_test_results :
      platform_name => {
        compatible = result.passed
        platform = result.platform
        test_result = result.passed ? "pass" : "fail"
      }
    }

    quality_gates = {
      critical_tests_pass = length([for test in local.ci_test_results : test if test.priority == "critical" && !test.passed]) == 0
      high_priority_tests_pass = length([for test in local.ci_test_results : test if test.priority == "high" && !test.passed]) == 0
      platform_compatibility_pass = alltrue([for test in local.platform_test_results : test.passed])
      overall_quality_gate = local.ci_summary.all_tests_passed
    }

    recommendations = local.ci_summary.all_tests_passed ? [
      "✅ All CI/CD tests passed - ready for deployment",
      "✅ Private state encryption working correctly across platforms",
      "🚀 Proceed with release pipeline",
      "📊 Monitor production deployment"
    ] : concat([
      "❌ CI/CD tests failed - deployment blocked",
      "🔧 Fix failing tests before proceeding"
    ], local.ci_summary.critical_failures > 0 ? [
      "🚨 Critical failures detected - immediate attention required"
    ] : [], [
      "📋 Review test results and implement fixes",
      "🔄 Re-run tests after remediation"
    ])

    artifacts = {
      junit_report = pyvider_file_content.junit_test_report.filename
      github_workflow = pyvider_file_content.github_actions_workflow.filename
      jenkins_pipeline = pyvider_file_content.jenkins_pipeline.filename
      test_report = pyvider_file_content.cicd_test_report.filename
    }
  })
}

output "cicd_testing_results" {
  description = "CI/CD integration testing results for private state verification"
  value = {
    execution_summary = {
      ci_environment = var.ci_environment
      build_number = var.build_number
      test_suite_name = var.test_suite.name
      execution_status = local.ci_summary.ci_status
      exit_code = local.ci_summary.exit_code
    }

    test_metrics = {
      total_tests = local.ci_summary.overall_tests_passed + local.ci_summary.overall_tests_failed
      passed_tests = local.ci_summary.overall_tests_passed
      failed_tests = local.ci_summary.overall_tests_failed
      success_rate = local.ci_summary.overall_tests_failed == 0 ? 100 : (local.ci_summary.overall_tests_passed / (local.ci_summary.overall_tests_passed + local.ci_summary.overall_tests_failed)) * 100
    }

    test_breakdown = {
      matrix_tests = {
        total = local.ci_summary.total_matrix_tests
        passed = local.ci_summary.matrix_tests_passed
        failed = local.ci_summary.matrix_tests_failed
      }
      platform_tests = {
        total = local.ci_summary.total_platform_tests
        passed = local.ci_summary.platform_tests_passed
        failed = local.ci_summary.platform_tests_failed
      }
    }

    quality_gates = {
      critical_tests_pass = local.ci_summary.critical_failures == 0
      all_tests_pass = local.ci_summary.all_tests_passed
      deployment_approved = local.ci_summary.all_tests_passed
    }

    platform_compatibility = {
      for platform_name, result in local.platform_test_results :
      platform_name => result.passed
    }

    artifacts_generated = [
      pyvider_file_content.junit_test_report.filename,
      pyvider_file_content.github_actions_workflow.filename,
      pyvider_file_content.jenkins_pipeline.filename,
      pyvider_file_content.cicd_test_report.filename
    ]
  }
}