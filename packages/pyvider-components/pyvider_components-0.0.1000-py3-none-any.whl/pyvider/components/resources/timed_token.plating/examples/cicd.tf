# CI/CD pipeline token examples

# Example 1: GitHub Actions deployment token
resource "pyvider_timed_token" "github_deploy" {
  name = "github-actions-deployment"
}

# Create GitHub Actions configuration
resource "pyvider_file_content" "github_actions_config" {
  filename = "/tmp/github_actions_config.yaml"
  content = yamlencode({
    deployment = {
      token_info = {
        name = pyvider_timed_token.github_deploy.name
        id = pyvider_timed_token.github_deploy.id
        expires_at = pyvider_timed_token.github_deploy.expires_at
        token_available = pyvider_timed_token.github_deploy.token != null
      }
      environment = "production"
      deployment_strategy = "rolling"
      timeout_minutes = 30
    }

    workflow = {
      name = "Deploy to Production"
      on = {
        push = {
          branches = ["main"]
        }
      }
      jobs = {
        deploy = {
          "runs-on" = "ubuntu-latest"
          steps = [
            {
              name = "Checkout code"
              uses = "actions/checkout@v3"
            },
            {
              name = "Deploy with temporary token"
              run = "deploy.sh"
              env = {
                DEPLOY_TOKEN_ID = pyvider_timed_token.github_deploy.id
                DEPLOY_TOKEN_EXPIRES = pyvider_timed_token.github_deploy.expires_at
              }
            }
          ]
        }
      }
    }
  })
}

# Example 2: Jenkins pipeline token
resource "pyvider_timed_token" "jenkins_build" {
  name = "jenkins-build-pipeline"
}

# Create Jenkins pipeline configuration
resource "pyvider_file_content" "jenkins_config" {
  filename = "/tmp/Jenkinsfile.config"
  content = join("\n", [
    "// Jenkins Pipeline Configuration",
    "// Generated with temporary token: ${pyvider_timed_token.jenkins_build.id}",
    "",
    "pipeline {",
    "    agent any",
    "    ",
    "    environment {",
    "        BUILD_TOKEN_ID = '${pyvider_timed_token.jenkins_build.id}'",
    "        BUILD_TOKEN_NAME = '${pyvider_timed_token.jenkins_build.name}'",
    "        TOKEN_EXPIRES_AT = '${pyvider_timed_token.jenkins_build.expires_at}'",
    "    }",
    "    ",
    "    stages {",
    "        stage('Validate Token') {",
    "            steps {",
    "                script {",
    "                    echo \"Using token: ${pyvider_timed_token.jenkins_build.name}\"",
    "                    echo \"Token ID: ${pyvider_timed_token.jenkins_build.id}\"",
    "                    echo \"Expires at: ${pyvider_timed_token.jenkins_build.expires_at}\"",
    "                    ",
    "                    // Validate token is available",
    "                    if (!env.BUILD_TOKEN_ID) {",
    "                        error('Build token is not available')",
    "                    }",
    "                }",
    "            }",
    "        }",
    "        ",
    "        stage('Build') {",
    "            steps {",
    "                echo 'Building application with temporary credentials...'",
    "                // Build steps would use the temporary token",
    "            }",
    "        }",
    "        ",
    "        stage('Test') {",
    "            steps {",
    "                echo 'Running tests with build token...'",
    "                // Test steps with token authentication",
    "            }",
    "        }",
    "        ",
    "        stage('Deploy') {",
    "            when {",
    "                branch 'main'",
    "            }",
    "            steps {",
    "                echo 'Deploying with temporary deployment token...'",
    "                // Deployment steps using the token",
    "            }",
    "        }",
    "    }",
    "    ",
    "    post {",
    "        always {",
    "            echo 'Pipeline completed. Token will expire automatically.'",
    "        }",
    "        failure {",
    "            echo 'Pipeline failed. Check token validity and expiration.'",
    "        }",
    "    }",
    "}"
  ])
}

# Example 3: GitLab CI/CD token
resource "pyvider_timed_token" "gitlab_ci" {
  name = "gitlab-ci-deployment"
}

# Create GitLab CI configuration
resource "pyvider_file_content" "gitlab_ci_config" {
  filename = "/tmp/gitlab-ci.yml"
  content = yamlencode({
    stages = ["build", "test", "deploy"]

    variables = {
      CI_TOKEN_NAME = pyvider_timed_token.gitlab_ci.name
      CI_TOKEN_ID = pyvider_timed_token.gitlab_ci.id
      TOKEN_EXPIRES_AT = pyvider_timed_token.gitlab_ci.expires_at
    }

    before_script = [
      "echo \"Using CI token: $CI_TOKEN_NAME\"",
      "echo \"Token expires at: $TOKEN_EXPIRES_AT\"",
      "# Token validation would happen here"
    ]

    build = {
      stage = "build"
      script = [
        "echo \"Building with token ID: $CI_TOKEN_ID\"",
        "# Build commands using the temporary token"
      ]
      artifacts = {
        paths = ["dist/"]
        expire_in = "1 hour"
      }
    }

    test = {
      stage = "test"
      script = [
        "echo \"Testing with temporary credentials\"",
        "# Test commands with token authentication"
      ]
      dependencies = ["build"]
    }

    deploy = {
      stage = "deploy"
      script = [
        "echo \"Deploying with token: $CI_TOKEN_NAME\"",
        "echo \"Deployment token expires: $TOKEN_EXPIRES_AT\"",
        "# Deployment commands using the token"
      ]
      only = ["main"]
      when = "manual"
    }
  })
}

# Example 4: Azure DevOps pipeline token
resource "pyvider_timed_token" "azure_devops" {
  name = "azure-devops-build"
}

# Create Azure DevOps pipeline configuration
resource "pyvider_file_content" "azure_pipeline_config" {
  filename = "/tmp/azure-pipelines.yml"
  content = join("\n", [
    "# Azure DevOps Pipeline",
    "# Token: ${pyvider_timed_token.azure_devops.name}",
    "# Token ID: ${pyvider_timed_token.azure_devops.id}",
    "# Expires: ${pyvider_timed_token.azure_devops.expires_at}",
    "",
    "trigger:",
    "  branches:",
    "    include:",
    "      - main",
    "      - develop",
    "",
    "variables:",
    "  buildTokenId: '${pyvider_timed_token.azure_devops.id}'",
    "  buildTokenName: '${pyvider_timed_token.azure_devops.name}'",
    "  tokenExpiresAt: '${pyvider_timed_token.azure_devops.expires_at}'",
    "",
    "stages:",
    "  - stage: Build",
    "    displayName: 'Build Application'",
    "    jobs:",
    "      - job: BuildJob",
    "        displayName: 'Build with Temporary Token'",
    "        pool:",
    "          vmImage: 'ubuntu-latest'",
    "        steps:",
    "          - script: |",
    "              echo \"Using build token: $(buildTokenName)\"",
    "              echo \"Token ID: $(buildTokenId)\"",
    "              echo \"Token expires: $(tokenExpiresAt)\"",
    "              # Build commands would use the temporary token",
    "            displayName: 'Build Application'",
    "",
    "  - stage: Test",
    "    displayName: 'Run Tests'",
    "    dependsOn: Build",
    "    jobs:",
    "      - job: TestJob",
    "        displayName: 'Test with Token Authentication'",
    "        pool:",
    "          vmImage: 'ubuntu-latest'",
    "        steps:",
    "          - script: |",
    "              echo \"Running tests with token: $(buildTokenName)\"",
    "              # Test commands with token authentication",
    "            displayName: 'Run Tests'",
    "",
    "  - stage: Deploy",
    "    displayName: 'Deploy to Production'",
    "    dependsOn: Test",
    "    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))",
    "    jobs:",
    "      - deployment: DeployJob",
    "        displayName: 'Deploy with Temporary Credentials'",
    "        environment: 'production'",
    "        strategy:",
    "          runOnce:",
    "            deploy:",
    "              steps:",
    "                - script: |",
    "                    echo \"Deploying with token: $(buildTokenName)\"",
    "                    echo \"Token expires at: $(tokenExpiresAt)\"",
    "                    # Deployment commands using the token",
    "                  displayName: 'Deploy Application'"
  ])
}

# Example 5: CircleCI configuration token
resource "pyvider_timed_token" "circleci" {
  name = "circleci-workflow"
}

# Create CircleCI configuration
resource "pyvider_file_content" "circleci_config" {
  filename = "/tmp/circleci_config.yml"
  content = yamlencode({
    version = "2.1"

    executors = {
      default = {
        docker = [
          {
            image = "cimg/node:18.0"
          }
        ]
        environment = {
          CI_TOKEN_NAME = pyvider_timed_token.circleci.name
          CI_TOKEN_ID = pyvider_timed_token.circleci.id
          TOKEN_EXPIRES_AT = pyvider_timed_token.circleci.expires_at
        }
      }
    }

    jobs = {
      build = {
        executor = "default"
        steps = [
          "checkout",
          {
            run = {
              name = "Validate Token"
              command = join("\n", [
                "echo \"Using CircleCI token: $CI_TOKEN_NAME\"",
                "echo \"Token ID: $CI_TOKEN_ID\"",
                "echo \"Expires at: $TOKEN_EXPIRES_AT\"",
                "# Token validation logic here"
              ])
            }
          },
          {
            run = {
              name = "Build Application"
              command = join("\n", [
                "echo \"Building with temporary token\"",
                "# Build commands using the token"
              ])
            }
          }
        ]
      }

      test = {
        executor = "default"
        steps = [
          "checkout",
          {
            run = {
              name = "Run Tests"
              command = join("\n", [
                "echo \"Testing with token: $CI_TOKEN_NAME\"",
                "# Test commands with token authentication"
              ])
            }
          }
        ]
      }

      deploy = {
        executor = "default"
        steps = [
          "checkout",
          {
            run = {
              name = "Deploy to Production"
              command = join("\n", [
                "echo \"Deploying with token: $CI_TOKEN_NAME\"",
                "echo \"Token expires: $TOKEN_EXPIRES_AT\"",
                "# Deployment commands using the token"
              ])
            }
          }
        ]
      }
    }

    workflows = {
      build_test_deploy = {
        jobs = [
          "build",
          {
            test = {
              requires = ["build"]
            }
          },
          {
            deploy = {
              requires = ["test"]
              filters = {
                branches = {
                  only = ["main"]
                }
              }
            }
          }
        ]
      }
    }
  })
}

# Create CI/CD token management summary
resource "pyvider_file_content" "cicd_token_summary" {
  filename = "/tmp/cicd_token_summary.json"
  content = jsonencode({
    timestamp = timestamp()

    ci_cd_tokens = {
      github_actions = {
        token_name = pyvider_timed_token.github_deploy.name
        token_id = pyvider_timed_token.github_deploy.id
        expires_at = pyvider_timed_token.github_deploy.expires_at
        platform = "GitHub Actions"
        use_case = "Production deployment"
      }

      jenkins = {
        token_name = pyvider_timed_token.jenkins_build.name
        token_id = pyvider_timed_token.jenkins_build.id
        expires_at = pyvider_timed_token.jenkins_build.expires_at
        platform = "Jenkins"
        use_case = "Build pipeline"
      }

      gitlab_ci = {
        token_name = pyvider_timed_token.gitlab_ci.name
        token_id = pyvider_timed_token.gitlab_ci.id
        expires_at = pyvider_timed_token.gitlab_ci.expires_at
        platform = "GitLab CI/CD"
        use_case = "CI/CD deployment"
      }

      azure_devops = {
        token_name = pyvider_timed_token.azure_devops.name
        token_id = pyvider_timed_token.azure_devops.id
        expires_at = pyvider_timed_token.azure_devops.expires_at
        platform = "Azure DevOps"
        use_case = "Build and deployment"
      }

      circleci = {
        token_name = pyvider_timed_token.circleci.name
        token_id = pyvider_timed_token.circleci.id
        expires_at = pyvider_timed_token.circleci.expires_at
        platform = "CircleCI"
        use_case = "Workflow automation"
      }
    }

    security_features = {
      automatic_expiration = true
      sensitive_data_protection = true
      platform_agnostic = true
      no_permanent_credentials = true
    }

    best_practices = [
      "Use environment variables for token IDs",
      "Validate token availability before use",
      "Monitor token expiration times",
      "Plan for token rotation",
      "Never commit actual token values to repository",
      "Use tokens only for the duration needed"
    ]

    recommendations = {
      token_rotation = "Implement automated token rotation for production workloads"
      monitoring = "Set up alerts before token expiration"
      security = "Audit token usage and access patterns"
      documentation = "Document token lifecycle and responsibilities"
    }
  })
}

output "cicd_token_configurations" {
  description = "CI/CD platform token configurations"
  value = {
    platforms_configured = ["GitHub Actions", "Jenkins", "GitLab CI/CD", "Azure DevOps", "CircleCI"]

    tokens_created = {
      github_actions = {
        name = pyvider_timed_token.github_deploy.name
        id = pyvider_timed_token.github_deploy.id
        expires_at = pyvider_timed_token.github_deploy.expires_at
      }
      jenkins = {
        name = pyvider_timed_token.jenkins_build.name
        id = pyvider_timed_token.jenkins_build.id
        expires_at = pyvider_timed_token.jenkins_build.expires_at
      }
      gitlab_ci = {
        name = pyvider_timed_token.gitlab_ci.name
        id = pyvider_timed_token.gitlab_ci.id
        expires_at = pyvider_timed_token.gitlab_ci.expires_at
      }
      azure_devops = {
        name = pyvider_timed_token.azure_devops.name
        id = pyvider_timed_token.azure_devops.id
        expires_at = pyvider_timed_token.azure_devops.expires_at
      }
      circleci = {
        name = pyvider_timed_token.circleci.name
        id = pyvider_timed_token.circleci.id
        expires_at = pyvider_timed_token.circleci.expires_at
      }
    }

    configuration_files = [
      pyvider_file_content.github_actions_config.filename,
      pyvider_file_content.jenkins_config.filename,
      pyvider_file_content.gitlab_ci_config.filename,
      pyvider_file_content.azure_pipeline_config.filename,
      pyvider_file_content.circleci_config.filename,
      pyvider_file_content.cicd_token_summary.filename
    ]

    security_summary = {
      total_tokens = 5
      all_tokens_time_limited = true
      sensitive_values_protected = true
      automatic_expiration = true
    }
  }
}