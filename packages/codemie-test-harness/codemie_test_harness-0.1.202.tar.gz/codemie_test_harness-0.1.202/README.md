# CodeMie Test Harness

End-to-end, integration, and UI test suite for CodeMie services. This repository exercises CodeMie APIs (LLM, assistants, workflows, tools) and common integrations.

The suite is designed for high-parallel execution (pytest-xdist), resilient runs (pytest-rerunfailures), and optional reporting to ReportPortal.

## Table of Contents

- Part 1: codemie-test-harness command line (recommended)
  - Installation
  - Configuration (CLI)
  - Run with command line
  - Useful CLI commands and common markers
- Part 2: Contributors (pytest from repo)
  - Install and configure with .env (PREVIEW/AZURE/GCP/AWS/PROD/LOCAL)
  - Local with custom GitLab, GitHub, Jira and Confluence tokens
  - UI tests (Playwright)
  - ReportPortal integration
  - Makefile targets
  - Troubleshooting


## Part 1: codemie-test-harness command line (recommended)

### New Command Structure Overview

The CLI now provides four main command groups:

1. **`config`** - Comprehensive configuration management (10 categories, 86+ variables)
2. **`run`** - Enhanced test execution with flexible parameters
3. **`assistant`** - Direct assistant interaction and chat capabilities
4. **`workflow`** - Workflow execution
5. **`marks`** - List all available pytest marks in the test suite.

Each command group includes extensive help and validation features.

---

Use the CLI to install, configure, and run tests against your custom environment. No .env file is used in this flow. Values are stored in ~/.codemie/test-harness.json.

### Installation

Install from PyPI:

```shell
pip install codemie-test-harness
```

Tip: Use a virtual environment (e.g., python -m venv .venv && source .venv/bin/activate).

### Configuration (CLI)

The CLI provides comprehensive configuration management with **86+ environment variables** across **10 integration categories**. Configuration values are securely stored and support interactive setup, validation, and easy management.

#### Quick Setup

Set required Auth/API values once (saved under ~/.codemie/test-harness.json):

```shell
codemie-test-harness config set AUTH_SERVER_URL <auth_server_url>
codemie-test-harness config set AUTH_CLIENT_ID <client_id>
codemie-test-harness config set AUTH_CLIENT_SECRET <client_secret>
codemie-test-harness config set AUTH_REALM_NAME <realm_name>
codemie-test-harness config set CODEMIE_API_DOMAIN <codemie_api_domain_url>
```

Optional defaults for pytest:

```shell
codemie-test-harness config set PYTEST_MARKS "smoke"
codemie-test-harness config set PYTEST_N 8
codemie-test-harness config set PYTEST_RERUNS 2
codemie-test-harness config set PYTEST_COUNT 10  # For performance testing (optional)
```

#### Running Tests Locally (Minimal Configuration)

If you're running tests against a **local CodeMie instance** and want to use integration settings already stored in AWS Parameter Store (instead of configuring each integration manually), you only need to set these **4 minimal keys**:

```shell
# Minimal local setup - uses AWS Parameter Store for all integrations
codemie-test-harness config set AWS_ACCESS_KEY <your_aws_access_key>
codemie-test-harness config set AWS_SECRET_KEY <your_aws_secret_key>
codemie-test-harness config set CODEMIE_API_DOMAIN http://localhost:8080
codemie-test-harness config set TEST_USER_FULL_NAME "dev-codemie-user"
```

Then run your tests:

```shell
# Run all tests locally
codemie-test-harness run

# Run specific test categories
codemie-test-harness run --marks smoke
codemie-test-harness run --marks "api and not not_for_parallel_run" -n 8
```

**How it works:**
- The AWS credentials allow the test harness to automatically fetch integration credentials (GitLab, JIRA, Confluence, etc.) from AWS Parameter Store
- You don't need to manually configure individual integrations unless you want to override specific values
- All 86+ integration variables are automatically pulled from Parameter Store as needed
- This is ideal for local development and testing against your local CodeMie backend

**To override specific integrations locally:**

If you need to use your own tokens instead of shared Parameter Store values:

```shell
# Override with personal GitLab token
codemie-test-harness config set GITLAB_TOKEN <your_personal_token>

# Override with personal JIRA credentials
codemie-test-harness config set JIRA_TOKEN <your_personal_token>
```

Values set explicitly in the config take priority over AWS Parameter Store values.

#### Integration Categories & Management

The CLI supports **10 major integration categories** with comprehensive credential management:

1. **Version Control**: GitLab, GitHub
2. **Code Base**: SonarQube, SonarCloud
3. **Project Management**: JIRA (Server & Cloud), Confluence (Server & Cloud)
4. **Cloud Providers**: AWS, GCP, Azure Cloud, Kubernetes
5. **Azure DevOps**: Azure DevOps services
6. **Access Management**: Keycloak
7. **Notification Systems**: Email/Gmail, OAuth, Telegram
8. **Data Management**: SQL databases (MySQL, PostgreSQL, MSSQL), LiteLLM, Elasticsearch
9. **IT Service Management**: ServiceNow
10. **Quality Assurance**: Report Portal

#### Configuration Commands

**List and View Configurations:**
```shell
# List all available categories
codemie-test-harness config categories

# List variables for specific category
codemie-test-harness config vars version-control

# List all configurations (masked by default)
codemie-test-harness config list

# Show actual values (use with caution)
codemie-test-harness config list --show-values

# Get specific value
codemie-test-harness config get AUTH_SERVER_URL

# Show integration credentials by category
codemie-test-harness config integrations --category project-management
codemie-test-harness config integrations --show-values
```

**Interactive Setup:**
```shell
# Interactive setup for specific category
codemie-test-harness config setup --category version-control
codemie-test-harness config setup --category project-management

# Setup all categories interactively
codemie-test-harness config setup --all
```

**Validation:**
```shell
# Validate all configured credentials
codemie-test-harness config validate

# Validate specific category
codemie-test-harness config validate --category cloud
```

**Management:**
```shell
# Set individual values
codemie-test-harness config set KEY VALUE

# Remove specific keys
codemie-test-harness config unset --keys GITLAB_TOKEN,GITHUB_TOKEN

# Remove entire category
codemie-test-harness config unset --category version-control

# Clear all configuration (with confirmation)
codemie-test-harness config clear
codemie-test-harness config clear --force
```

#### Sample Integration Configurations

**Version Control:**
```shell
# Git provider selection
codemie-test-harness config set GIT_ENV gitlab   # or github

# GitLab
codemie-test-harness config set GITLAB_URL https://gitlab.example.com
codemie-test-harness config set GITLAB_TOKEN <gitlab_token>
codemie-test-harness config set GITLAB_PROJECT https://gitlab.example.com/group/project
codemie-test-harness config set GITLAB_PROJECT_ID 12345

# GitHub
codemie-test-harness config set GITHUB_URL https://github.com
codemie-test-harness config set GITHUB_TOKEN <github_token>
codemie-test-harness config set GITHUB_PROJECT https://github.com/org/repo
```

**Project Management:**
```shell
# JIRA Server
codemie-test-harness config set JIRA_URL https://jira.example.com
codemie-test-harness config set JIRA_TOKEN <jira_token>
codemie-test-harness config set JIRA_JQL "project = 'EPMCDME' and issuetype = 'Epic'"

# JIRA Cloud
codemie-test-harness config set JIRA_CLOUD_URL https://company.atlassian.net
codemie-test-harness config set JIRA_CLOUD_EMAIL user@company.com
codemie-test-harness config set JIRA_CLOUD_TOKEN <api_token>

# Confluence Server
codemie-test-harness config set CONFLUENCE_URL https://confluence.example.com
codemie-test-harness config set CONFLUENCE_TOKEN <confluence_token>
codemie-test-harness config set CONFLUENCE_CQL "space = EPMCDME and type = page"
```

**Cloud Providers:**
```shell
# AWS
codemie-test-harness config set AWS_ACCESS_KEY_ID <access_key>
codemie-test-harness config set AWS_SECRET_ACCESS_KEY <secret_key>
codemie-test-harness config set AWS_REGION us-east-1

# Azure
codemie-test-harness config set AZURE_CLIENT_ID <client_id>
codemie-test-harness config set AZURE_CLIENT_SECRET <client_secret>
codemie-test-harness config set AZURE_TENANT_ID <tenant_id>

# GCP
codemie-test-harness config set GCP_SA_KEY_BASE64 <base64_encoded_service_account>
```

**Quality Assurance:**
```shell
# Report Portal
codemie-test-harness config set RP_ENDPOINT https://rp.example.com
codemie-test-harness config set RP_PROJECT codemie_tests
codemie-test-harness config set RP_API_KEY <api_key>
```

#### Security Features

- **Credential Masking**: Sensitive values are masked by default in all displays
- **Show Values Flag**: Use `--show-values` only when needed to view actual credentials
- **Case Insensitive**: Configuration keys are case-insensitive for ease of use

**Notes:**
- Quoting is required for values with spaces (e.g., JQL/CQL)
- Resolution precedence when running: CLI flags > environment variables > saved config > defaults
- Config file path: ~/.codemie/test-harness.json
- All sensitive values are automatically masked in output unless `--show-values` is used

### Run with command line

#### Test Execution

Default run (uses saved config or defaults):

```shell
codemie-test-harness run
```

Override at runtime:

```shell
# Change marks, workers, reruns just for this run
codemie-test-harness run --marks "smoke or gitlab or jira_kb" -n 8 --reruns 2

# Run with specific environment settings
codemie-test-harness run --codemie-api-domain https://api.example.com --marks smoke

# Run with custom test patterns
codemie-test-harness run --test-path "tests/integration/" --marks api
```

Provider-specific examples:

```shell
# Only GitLab
codemie-test-harness run --marks gitlab

# Only GitHub
codemie-test-harness run --marks github

# Jira knowledge base
codemie-test-harness run --marks jira_kb

# Confluence knowledge base
codemie-test-harness run --marks confluence_kb

# Code knowledge base
codemie-test-harness --git-env gitlab run --marks code_kb

# Git tool
codemie-test-harness --git-env github run --marks git

# UI tests with specific browser
codemie-test-harness run --marks ui --headless
```

#### Advanced Marks Usage (Logical Operators)

Combine multiple markers using `and`, `or`, and `not` keywords for fine-grained test selection:

```shell
# OR operator - run tests with either marker
codemie-test-harness run --marks "smoke or gitlab" -n 8
codemie-test-harness run --marks "jira_kb or confluence_kb" -n 6

# AND operator - run tests with both markers
codemie-test-harness run --marks "api and smoke" -n 10
codemie-test-harness run --marks "gitlab and code_kb" -n 4

# NOT operator - exclude specific markers
codemie-test-harness run --marks "api and not ui" -n 10
codemie-test-harness run --marks "not not_for_parallel_run" -n 12

# Complex combinations with parentheses
codemie-test-harness run --marks "(smoke or api) and not ui" -n 8
codemie-test-harness run --marks "(gitlab or github) and not not_for_parallel_run" -n 10
codemie-test-harness run --marks "smoke and (jira_kb or confluence_kb)" -n 6

# Exclude multiple markers
codemie-test-harness run --marks "api and not (ui or not_for_parallel_run)" -n 10

# Run all knowledge base tests except code
codemie-test-harness run --marks "(jira_kb or confluence_kb) and not code_kb" -n 8
```

#### Performance and Load Testing

Run tests multiple times in parallel to simulate load and measure performance:

```shell
# Performance test: Run test 50 times with 10 parallel workers
codemie-test-harness run --marks excel_generation --count 50 -n 10

# Heavy load test: 100 iterations with 20 workers
codemie-test-harness run --marks excel_generation --count 100 -n 20 -v

# Light load test with retries for stability
codemie-test-harness run --marks smoke --count 25 -n 5 --reruns 2

# Set default count in config for repeated use
codemie-test-harness config set PYTEST_COUNT 30
codemie-test-harness run --marks excel_generation -n 10  # Uses count=30 from config

# Override config default for a specific run
codemie-test-harness run --marks excel_generation --count 100 -n 20  # Overrides config
```

**Note:** The `--count` parameter requires the `pytest-repeat` plugin, which is included in the dependencies.

#### Test Timeout Control

Control per-test timeout to prevent tests from running indefinitely. Tests exceeding the timeout will be **automatically terminated and marked as FAILED**.

**Configuration Priority**: CLI args → Environment variable → Config file → Default (300 seconds)

**Usage Examples:**

```shell
# Via CLI argument (600 seconds = 10 minutes)
codemie-test-harness run --timeout 600 --marks smoke

# Via config file (persistent)
codemie-test-harness config set TEST_TIMEOUT 900
codemie-test-harness run --marks api

# Via environment variable
export TEST_TIMEOUT=300
codemie-test-harness run --marks smoke

# Disable timeout for debugging (use 0)
codemie-test-harness run --timeout 0 --marks smoke

# Override config default for specific run
codemie-test-harness config set TEST_TIMEOUT 600
codemie-test-harness run --timeout 1200 --marks slow  # Uses 1200, not 600
```

**Default**: 300 seconds (5 minutes) per test

**What Happens on Timeout?**

When a test exceeds the configured timeout:
1. ✅ **Test is automatically terminated** - Execution stops immediately
2. ✅ **Marked as FAILED** - Test result shows as failed with clear timeout message
3. ✅ **Error details displayed** - Shows which test timed out and the configured limit
4. ✅ **Remaining tests continue** - Other tests proceed normally
5. ✅ **Stack trace captured** - Shows where the test was when timeout occurred

**Example timeout error output:**
```
FAILED tests/test_slow_operation.py::test_data_processing - Failed: Timeout >300.0s
```

**Notes:**
- Timeout applies to **individual test functions**, not the entire test run
- Useful for preventing hanging tests in CI/CD pipelines
- Consider increasing timeout for legitimate long-running operations (data processing, large file operations)
- Timeout of 0 disables the timeout (use for debugging only)

#### Assistant Chat Interface

Interact directly with CodeMie assistants through the CLI:

```shell
# Start new conversation with assistant
codemie-test-harness assistant chat --assistant-id "asst_123" -m "Hello, help me with testing"

# Continue existing conversation
codemie-test-harness assistant chat --assistant-id "asst_123" --conversation-id "conv_456" -m "What's next?"

# Chat with streaming enabled
codemie-test-harness assistant chat --assistant-id "asst_123" --stream -m "Generate test cases"

# Chat with Langfuse tracing
codemie-test-harness assistant chat --assistant-id "asst_123" --langfuse-traces-enabled -m "Analyze logs"
```

#### Workflow Execution

Execute CodeMie workflows directly from the command line:

```shell
# Execute workflow
codemie-test-harness workflow execute --workflow-id "wf_123"

# Execute workflow with user input
codemie-test-harness workflow execute --workflow-id "wf_456" --user-input "process test data"

# Execute workflow with custom execution ID
codemie-test-harness workflow execute --workflow-id "wf_789" --execution-id "exec_custom_001"
```

### Useful CLI commands and common markers

#### CLI Basics

```shell
# General help
codemie-test-harness --help

# Command-specific help
codemie-test-harness config --help
codemie-test-harness run --help
codemie-test-harness assistant --help
codemie-test-harness workflow --help

# Configuration management
codemie-test-harness config list
codemie-test-harness config get AUTH_SERVER_URL
codemie-test-harness config set PYTEST_N 12
codemie-test-harness config categories
codemie-test-harness config validate

# Quick configuration check
codemie-test-harness config integrations --category version-control
```

#### Advanced CLI Features

```shell
# Interactive category setup
codemie-test-harness config setup --category project-management

# Bulk configuration removal
codemie-test-harness config unset --keys "GITLAB_TOKEN,GITHUB_TOKEN"

# Validate specific integration
codemie-test-harness config validate --category cloud

# Show all variables for a category
codemie-test-harness config vars data-management

# Test execution with multiple overrides
codemie-test-harness run --marks "smoke and not ui" -n 10 --reruns 3 --headless

# Performance testing with count parameter
codemie-test-harness run --marks excel_generation --count 50 -n 10
```

#### Common Test Markers

Common markers in this repo include:
- **smoke** - Quick smoke tests
- **mcp** - Model Context Protocol tests
- **plugin** - Plugin functionality tests
- **api** - Comprehensive api tests
- **ui** - User interface tests (Playwright)
- **jira_kb, confluence_kb, code_kb** - Knowledge base tests
- **gitlab, github, git** - Version control integration tests
- **not_for_parallel_run** - Tests that must run sequentially

#### Environment-Specific Execution

```shell
# Target specific environments
codemie-test-harness run --codemie-api-domain https://preview.codemie.ai --marks smoke
codemie-test-harness run --codemie-api-domain https://prod.codemie.ai --marks api

# Local development
codemie-test-harness run --codemie-api-domain http://localhost:8080 --marks "smoke and not ui"
```

---

## Part 2: Contributors (pytest from repo)

This section is for contributors who run tests from a cloned codemie-sdk repository (test-harness package). This flow uses a .env file and may pull values from AWS SSM Parameter Store.

### Credentials Management System

The test harness uses a sophisticated **unified credentials management system** that handles integration credentials through a **priority-based resolution approach**:

#### **Resolution Priority (Highest to Lowest):**

1. **Environment Variables (.env file)** - Highest priority
2. **AWS Parameter Store** - Fallback with JSON path navigation  
3. **Default Values** - Final fallback

#### **AWS Parameter Store Integration**

The credentials manager automatically integrates with AWS Parameter Store using **JSON path navigation** for structured credential storage:

**Parameter Structure:**
- **Base Path**: `/codemie/autotests/integrations/`
- **Service Groupings**: `jira`, `confluence`, `git`, `aws`, `azure`, `gcp`, `sonar`, etc.
- **JSON Path Navigation**: Uses dot notation (e.g., `jira_server.url`, `jira_cloud.token`)

**Example AWS Parameter Store Structure:**
```json
{
  "jira_server": {
    "url": "https://jira.example.com",
    "token": "server_token_here",
    "jql": "project = 'EPMCDME'"
  },
  "jira_cloud": {
    "url": "https://company.atlassian.net",
    "email": "user@company.com",
    "token": "cloud_token_here",
    "jql": "project = 'CLOUD' and status = 'Open'"
  }
}
```

**Environment-Aware Credential Resolution:**
- **Preview Environment**: Uses standard paths (e.g., `elasticsearch.*`, `preview.mysql.*`)
- **Sandbox Environments** (Azure/GCP/AWS): Uses sandbox-specific paths (e.g., `sandbox.elasticsearch.*`, `sandbox.mysql.*`)
- **Automatic Detection**: Environment resolver determines the appropriate credential set

#### **Supported Integration Categories**

The credentials manager supports **86+ environment variables** across **10 categories**:

1. **Version Control**: GitLab, GitHub (tokens, project IDs, URLs)
2. **Project Management**: JIRA Server/Cloud, Confluence Server/Cloud (tokens, JQL, CQL)
3. **Cloud Providers**: AWS (keys, regions), Azure (client credentials), GCP (service accounts)
4. **Code Quality**: SonarQube Server/Cloud (tokens, project keys)
5. **DevOps**: Azure DevOps (PATs, organization/project names)
6. **Access Management**: Keycloak (client credentials, realms)
7. **Notifications**: Email/Gmail (SMTP), OAuth (refresh tokens), Telegram (bot tokens)
8. **Data Management**: SQL databases (MySQL, PostgreSQL, MSSQL), Elasticsearch, LiteLLM
9. **IT Service**: ServiceNow (API keys)
10. **Quality Assurance**: Report Portal (API keys, projects), Kubernetes (bearer tokens)


### Install and configure with .env (PREVIEW/AZURE/GCP/AWS/PROD/LOCAL)

1) Clone the codemie-sdk repository and navigate to the test-harness folder.
2) Create a .env file in the project root. If you provide AWS credentials, the suite will fetch additional values from AWS Systems Manager Parameter Store and recreate .env accordingly.

```properties
CODEMIE_API_DOMAIN=http://localhost:8080

AWS_ACCESS_KEY=<aws_access_token>
AWS_SECRET_KEY=<aws_secret_key>
```

### Local with custom GitLab, GitHub, Jira and Confluence tokens

1) Start from a .env populated via AWS (optional)
2) Replace the tokens below with your personal values
3) Add variables to integrations with your personal values (optional)
4) Important: After replacing tokens, remove AWS_ACCESS_KEY and AWS_SECRET_KEY from .env — otherwise they will overwrite your changes next time .env is regenerated

Full .env example:

```properties
PROJECT_NAME=codemie
GIT_ENV=gitlab # required for e2e tests only
DEFAULT_TIMEOUT=60
CLEANUP_DATA=True
LANGFUSE_TRACES_ENABLED=False

CODEMIE_API_DOMAIN=http://localhost:8080

FRONTEND_URL=https://localhost:5173/
HEADLESS=False

NATS_URL=nats://localhost:4222

TEST_USER_FULL_NAME=dev-codemie-user

RP_API_KEY=<report_portal_api_key>
```

Now you can run full or subset packs. Examples:

```shell
# All tests except tests that cannot be run in parallel (-n controls the number of workers)
pytest -n 10 -m "not not_for_parallel_run" --reruns 2

# Tests that cannot be run in parallel
pytest -m not_for_parallel_run --reruns 2

# API tests
pytest -n 10 -m "api and not not_for_parallel_run" --reruns 2
pytest -m not_for_parallel_run --reruns 3

# Performance/Load testing: Run test multiple times in parallel
pytest -n 10 --count 50 -m excel_generation  # Run 50 times with 10 workers
pytest -n 20 --count 100 -m smoke --reruns 2  # Heavy load with retries
```

**Advanced Marks Usage with Logical Operators:**

Combine markers using `and`, `or`, and `not` for precise test selection:

```shell
# OR operator - run tests with either marker
pytest -n 8 -m "smoke or gitlab" --reruns 2
pytest -n 6 -m "jira_kb or confluence_kb" --reruns 2

# AND operator - run tests with both markers
pytest -n 10 -m "api and smoke" --reruns 2
pytest -n 4 -m "gitlab and code_kb" --reruns 2

# NOT operator - exclude specific markers
pytest -n 10 -m "api and not ui" --reruns 2
pytest -n 12 -m "not not_for_parallel_run" --reruns 2

# Complex combinations with parentheses
pytest -n 8 -m "(smoke or api) and not ui" --reruns 2
pytest -n 10 -m "(gitlab or github) and not not_for_parallel_run" --reruns 2
pytest -n 6 -m "smoke and (jira_kb or confluence_kb)" --reruns 2

# Exclude multiple markers
pytest -n 10 -m "api and not (ui or not_for_parallel_run)" --reruns 2

# Run all knowledge base tests except code KB
pytest -n 8 -m "(jira_kb or confluence_kb) and not code_kb" --reruns 2

# Run all Git-related tests (GitLab or GitHub)
pytest -n 8 -m "gitlab or github or git" --reruns 2
```

**Notes:**
- `--reruns 2` uses pytest-rerunfailures to improve resiliency in flaky environments
- `--count N` uses pytest-repeat to run each test N times (useful for performance/load testing)
- Use quotes around marker expressions containing spaces or special characters

#### Test Timeout Configuration

Tests have a configurable timeout to prevent hanging. Default is **300 seconds (5 minutes)** per test.

**Configure in .env file:**
```properties
TEST_TIMEOUT=600  # 10 minutes
```

**Override via pytest CLI:**
```shell
# Set timeout for this run
pytest -n 10 -m smoke --timeout 900  # 15 minutes

# Disable timeout (debugging)
pytest -m slow_tests --timeout 0

# Use default from .env or pytest.ini
pytest -n 10 -m api  # Uses TEST_TIMEOUT from .env or 300s default
```

**Timeout Behavior:**

When a test exceeds the configured timeout:
- Test execution is **terminated immediately**
- Test is marked as **FAILED** with a timeout error message
- Stack trace shows where the test was when timeout occurred
- Remaining tests continue execution normally

**Example timeout failure:**
```
================================== FAILURES ===================================
_________________ test_slow_workflow_execution ________________

E   Failed: Timeout >300.0s

tests/workflow/test_workflows.py:145: Failed
```

**Best Practices:**
- Keep default timeout reasonable (5-10 minutes for E2E tests)
- Increase timeout for specific slow tests using `@pytest.mark.timeout(900)`
- Use timeout=0 only for debugging hanging tests
- Consider if a test legitimately needs > 5 minutes (optimize if possible)

### UI tests (Playwright)

Install browsers once:

```shell
playwright install
```

Then run UI pack:

```shell
pytest -n 4 -m ui --reruns 2
```

Playwright docs: https://playwright.dev/python/docs/intro

### ReportPortal integration

pytest.ini is preconfigured with rp_endpoint, rp_project, and a default rp_launch. To publish results:

1) Set RP_API_KEY in .env
2) Add the flag:

```shell
pytest -n 10 -m "api and not not_for_parallel_run" --reruns 2 --reportportal
```

If you need access to the ReportPortal project, contact: Anton Yeromin (anton_yeromin@epam.com).

### Makefile targets

- install — poetry install
- ruff — lint and format with Ruff
- ruff-format — format only
- ruff-fix — apply autofixes
- build — poetry build
- publish — poetry publish

Example:

```shell
make install
make ruff
```

### Troubleshooting

- Playwright not installed: Run playwright install.
- Headless issues locally: Set HEADLESS=True in .env for CI or False for local debugging.
- Env values keep reverting: Ensure AWS_ACCESS_KEY and AWS_SECRET_KEY are removed after manual edits to .env.
- Authentication failures: Verify AUTH_* variables and CODEMIE_API_DOMAIN are correct for the target environment.
- Slow or flaky runs: Reduce -n, increase timeouts, and/or use --reruns.
