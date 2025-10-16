# DevOps MCP Server

[![PyPI version](https://badge.fury.io/py/devops-mcps.svg)](https://badge.fury.io/py/devops-mcps)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-97.38%25-brightgreen.svg)](https://github.com/huangjien/devops-mcps)

A [FastMCP](https://github.com/modelcontextprotocol/fastmcp)-based MCP server providing a suite of DevOps tools and integrations.

This server operates in a read-only manner, retrieving data for analysis and display without modifying your systems. It's designed with safety in mind for DevOps environments.

Certified by [MCP Review](https://mcpreview.com/mcp-servers/huangjien/devops-mcps)

## Features

The DevOps MCP Server integrates with various essential DevOps platforms:

### GitHub Integration

-   **Repository Management**: Search and view repository details.
-   **File Access**: Retrieve file contents from repositories.
-   **Issue Tracking**: Manage and track issues.
-   **Code Search**: Perform targeted code searches.
-   **Commit History**: View commit history for branches.
-   **Public & Enterprise Support**: Automatically detects and connects to both public GitHub and GitHub Enterprise instances (configurable via `GITHUB_API_URL`).

### Jenkins Integration

-   **Job Management**: List and manage Jenkins jobs.
-   **Build Logs**: Retrieve and analyze build logs.
-   **View Management**: Access and manage Jenkins views.
-   **Build Parameters**: Inspect parameters used for builds.
-   **Failure Monitoring**: Identify and monitor recent failed builds.

### Artifactory Integration

-   **Repository Browsing**: List items (files and directories) within Artifactory repositories.
-   **Artifact Search**: Search for artifacts by name or path across multiple repositories using Artifactory Query Language (AQL).
-   **Item Details**: Retrieve metadata and properties for specific files and directories.
-   **Authentication**: Supports both token-based and username/password authentication.

## Installation

Install the package using pip:

```bash
pip install devops-mcps
```

## Usage

Run the MCP server directly:

```bash
devops-mcps
```

### Transport Configuration

The server supports two communication transport types:

-   `stdio` (default): Standard input/output.
-   `stream_http`: HTTP streaming transport.

**Local Usage:**

```bash
# Default stdio transport
devops-mcps

# stream_http transport (runs HTTP server on 127.0.0.1:3721/mcp by default)
devops-mcps --transport stream_http
```

**UVX Usage:**

If using [UVX](https://github.com/modelcontextprotocol/uvx), first install the tools:

```bash
uvx install
```

Then run:

```bash
# Default stdio transport
uvx run devops-mcps

# stream_http transport
uvx run devops-mcps-stream-http
```

## Configuration

Configure the server using environment variables:

**Required:**

```bash
# GitHub
export GITHUB_PERSONAL_ACCESS_TOKEN="your_github_token"
# Optional: For GitHub Enterprise, set your API endpoint
# export GITHUB_API_URL="https://github.mycompany.com"

# Jenkins
export JENKINS_URL="your_jenkins_url"
export JENKINS_USER="your_jenkins_username"
export JENKINS_TOKEN="your_jenkins_api_token_or_password"

# Artifactory
export ARTIFACTORY_URL="https://your-artifactory-instance.example.com"
# Choose ONE authentication method:
export ARTIFACTORY_IDENTITY_TOKEN="your_artifactory_identity_token"
# OR
export ARTIFACTORY_USERNAME="your_artifactory_username"
export ARTIFACTORY_PASSWORD="your_artifactory_password"
```

**Optional:**

```bash
# Jenkins Log Length (default: 5120 bytes)
export LOG_LENGTH=10240

# MCP Server Port for stream_http transport (default: 3721)
export MCP_PORT=3721

# Dynamic Prompts (optional)
export PROMPTS_FILE="example_prompts.json"
```

**Note**: `LOG_LENGTH` controls the amount of Jenkins log data retrieved. Adjust as needed.

**Alternative: Using .env file**

You can also create a `.env` file in the project root directory instead of setting environment variables manually:

```bash
# .env file
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
PROMPTS_FILE=example_prompts.json
# Add other optional environment variables as needed
```

The server will automatically load environment variables from the `.env` file when it starts.

### Dynamic Prompts

The server supports loading custom prompts from a JSON file. Set the `PROMPTS_FILE` environment variable to the path of your prompts configuration file.

**Prompts File Format:**

```json
{
  "prompts": [
    {
      "name": "github_repo_analysis",
      "description": "Analyze a GitHub repository for DevOps insights",
      "template": "Please analyze the GitHub repository {{owner}}/{{repo}} and provide insights on:\n\n1. Repository structure and organization\n2. CI/CD pipeline configuration\n3. Code quality indicators\n4. Security considerations\n5. Documentation quality\n\n{{#include_issues}}Also include analysis of recent issues and their resolution patterns.{{/include_issues}}",
      "arguments": [
        {
          "name": "owner",
          "description": "GitHub repository owner",
          "required": true
        },
        {
          "name": "repo",
          "description": "GitHub repository name",
          "required": true
        },
        {
          "name": "include_issues",
          "description": "Include analysis of repository issues",
          "required": false
        }
      ]
    }
  ]
}
```

### Using Prompts

The DevOps MCP Server provides dynamic prompts that help you perform common DevOps tasks. Here's how to use the available prompts:

#### Available Prompts

1. **`quick_repo_check`** - Comprehensive repository health assessment with security analysis
2. **`daily_check`** - Complete DevOps monitoring with Jenkins job analysis and infrastructure status
3. **`build_troubleshoot`** - Advanced build failure investigation with root cause analysis

#### Using the `daily_check` Prompt

**Purpose:** Comprehensive DevOps monitoring and infrastructure status reporting with Jenkins job analysis.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `time_range` | string | ❌ No | Time range for analysis (e.g., "24h", "7d", "1w") |
| `include_infrastructure` | boolean | ❌ No | Include infrastructure status in the report |
| `focus_area` | string | ❌ No | Specific area to focus on (e.g., "builds", "deployments", "security") |

**Usage Examples:**

```
# Basic daily monitoring
Prompt: daily_check

# Weekly infrastructure review
Prompt: daily_check
Parameters:
- time_range: "7d"
- include_infrastructure: true

# Focus on build failures
Prompt: daily_check
Parameters:
- time_range: "24h"
- focus_area: "builds"
```

**What it does:**
1. 🔍 **Jenkins Job Analysis**: Comprehensive review of job statuses and recent failures
2. 🔧 **Root Cause Investigation**: Deep dive into failure patterns and trends
3. 🏗️ **Infrastructure Status**: Health check of critical infrastructure components
4. 📋 **Actionable Recommendations**: Prioritized action items with implementation guidance
5. 📊 **Executive Summary**: High-level overview with key metrics and trends

#### Using the `build_troubleshoot` Prompt

**Purpose:** Advanced build failure investigation with comprehensive root cause analysis and actionable recommendations.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_name` | string | ✅ Yes | Jenkins job name |
| `build_number` | string | ❌ No | Build number to analyze (use -1 for latest) |
| `include_logs` | boolean | ❌ No | Whether to include build logs in analysis |

**Usage Examples:**

```
# Basic usage (latest build)
Prompt: build_troubleshoot
Parameters:
- job_name: "my-application-build"

# Specific build number
Prompt: build_troubleshoot
Parameters:
- job_name: "my-application-build"
- build_number: "42"

# With build logs
Prompt: build_troubleshoot
Parameters:
- job_name: "my-application-build"
- build_number: "42"
- include_logs: true
```

**What it does:**
1. Gets build status and basic information for the specified job
2. Retrieves and analyzes build logs (if `include_logs` is true)
3. Identifies potential failure causes based on the build data
4. Suggests troubleshooting steps with actionable recommendations

#### Using the `quick_repo_check` Prompt

**Purpose:** Comprehensive repository health assessment with security analysis and DevOps best practices evaluation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repo_name` | string | ✅ Yes | Repository name in format 'owner/repo' |
| `include_security` | boolean | ❌ No | Include security analysis in the assessment |
| `check_ci_cd` | boolean | ❌ No | Analyze CI/CD pipeline configuration |

**Usage Examples:**

```
# Basic repository check
Prompt: quick_repo_check
Parameters:
- repo_name: "facebook/react"

# Comprehensive security assessment
Prompt: quick_repo_check
Parameters:
- repo_name: "myorg/myproject"
- include_security: true
- check_ci_cd: true
```

**What it does:**
1. 📊 **Repository Health Assessment**: Comprehensive evaluation of repository status and metrics
2. 🔒 **Security Analysis**: Security configuration review and vulnerability assessment
3. 🏗️ **CI/CD Pipeline Evaluation**: Analysis of build and deployment configurations
4. 📋 **Actionable Recommendations**: Prioritized improvement suggestions with implementation guidance
5. 📈 **Executive Summary**: High-level overview with key findings and strategic recommendations

#### Natural Language Support

The DevOps MCP Server supports both **structured** and **natural language** approaches for invoking prompts:

**Structured Format (Explicit):**
```
Use prompt: build_troubleshoot
Parameters:
- job_name: "creole-Automerge-main"
- build_number: 29
- include_logs: true
```

**Natural Language Format (Recommended):**
```
"Perform daily DevOps monitoring check for the last 24 hours"

"Troubleshoot the Jenkins build failure for job 'creole-Automerge-main' build #29 with detailed logs"

"Check the GitHub repository facebook/react with security analysis"

"Analyze the failed build for my-app-build job number 42 including logs"

"Run weekly infrastructure review with comprehensive monitoring"

"Assess repository health for myorg/myproject including CI/CD pipeline analysis"
```

**How Natural Language Processing Works:**

1. **Intent Recognition**: The AI assistant identifies which prompt matches your request
2. **Parameter Extraction**: Extracts specific values (job names, build numbers, repo names) from your message
3. **Automatic Mapping**: Maps your natural language to the structured prompt format
4. **Context Awareness**: Uses conversation history and workspace context for missing parameters

**Tips for Better Natural Language Recognition:**

- **Use Keywords**: Include terms like "troubleshoot", "analyze", "check repository", "build failure"
- **Be Specific**: Mention exact job names, build numbers, repository names
- **Use Quotes**: Put specific values in quotes for clarity (e.g., "my-job-name")
- **Include Context**: Specify what type of analysis you want

**Example Natural Language Patterns:**

| Intent | Natural Language Examples |
|--------|---------------------------|
| Daily Monitoring | "Daily DevOps check", "Run daily monitoring", "Infrastructure status report" |
| Repository Analysis | "Check repo owner/name with security", "Analyze GitHub repository X with CI/CD" |
| Build Troubleshooting | "Debug build failure", "Troubleshoot job X build Y", "Investigate build issues" |
| Include Logs | "with logs", "including detailed logs", "show build logs" |
| Latest Build | "latest build", "most recent build", "current build" |
| Time Range | "last 24 hours", "past week", "7 days", "weekly review" |
| Focus Areas | "focus on builds", "security analysis", "infrastructure review" |

#### Prerequisites

To use Jenkins-related prompts like `build_troubleshoot`, ensure you have:

```bash
# Required Jenkins environment variables
export JENKINS_URL="https://your-jenkins-server.com"
export JENKINS_USER="your-username"
export JENKINS_TOKEN="your-api-token"
```

To use GitHub-related prompts like `quick_repo_check`, ensure you have:

```bash
# Required GitHub environment variable
export GITHUB_PERSONAL_ACCESS_TOKEN="your_github_token"
```

**Template Variables:**
- Use `{{variable_name}}` for simple variable substitution
- Use `{{#variable_name}}...{{/variable_name}}` for conditional blocks (shown if variable has a value)
- Use `{{^variable_name}}...{{/variable_name}}` for negative conditional blocks (shown if variable is empty/null)

**Available Tools for Prompts:**
Your prompts can reference any of the available MCP tools:
- GitHub tools: `search_repositories`, `get_file_contents`, `list_commits`, `list_issues`, etc.
- Jenkins tools: `get_jenkins_jobs`, `get_jenkins_build_log`, `get_recent_failed_jenkins_builds`, etc.
- Azure tools: `get_azure_subscriptions`, `list_azure_vms`, `list_aks_clusters`, etc.
- Artifactory tools: `list_artifactory_items`, `search_artifactory_items`, `get_artifactory_item_info`, etc.

## Docker

Build the Docker image:

```bash
docker build -t devops-mcps .
```

Run the container:

```bash
# Stdio transport (interactive)
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="..." \
  -e JENKINS_URL="..." \
  -e JENKINS_USER="..." \
  -e JENKINS_TOKEN="..." \
  -e ARTIFACTORY_URL="..." \
  -e ARTIFACTORY_IDENTITY_TOKEN="..." \
  devops-mcps

# stream_http transport (background, HTTP server on 127.0.0.1:3721/mcp by default)
docker run -d -p 3721:3721 --rm \
  -e TRANSPORT_TYPE=stream_http \
  -e MCP_PORT=3721 \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="..." \
  -e JENKINS_URL="..." \
  -e JENKINS_USER="..." \
  -e JENKINS_TOKEN="..." \
  -e ARTIFACTORY_URL="..." \
  -e ARTIFACTORY_IDENTITY_TOKEN="..." \
  devops-mcps
```

Replace `...` with your actual credentials.

## VSCode Integration

Configure the MCP server in VSCode's `settings.json`:

**Example (UVX with stdio):**

```json
"devops-mcps": {
  "type": "stdio",
  "command": "uvx",
  "args": ["devops-mcps"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_...",
    "GITHUB_API_URL": "https://github.mycompany.com", // Optional for GHE
    "JENKINS_URL": "...",
    "JENKINS_USER": "...",
    "JENKINS_TOKEN": "...",
    "ARTIFACTORY_URL": "...",
    "ARTIFACTORY_IDENTITY_TOKEN": "cm..." // Or USERNAME/PASSWORD
  }
}
```

**Example (Docker with stream_http):**

Ensure the Docker container is running with stream_http enabled (see Docker section).

```json
{
  "type": "stream_http",
  "url": "http://127.0.0.1:3721/mcp", // Adjust if Docker host is remote or if MCP_PORT is set differently
  "env": {
    // Environment variables are set in the container,
    // but can be overridden here if needed.
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
  }
}
```

Refer to the initial `README.md` sections for other transport/runner combinations (UVX/stream_http, Docker/stdio).

## Development

Set up your development environment:

```bash
# Install dependencies (using uv)
uv pip install -e ".[dev]"
# Or sync with lock file
# uv sync --dev
```

**Linting and Formatting (Ruff):**

```bash
# Check code style
uvx ruff check .

# Format code
uvx ruff format .
```

**Testing (Pytest):**

```bash
# Run tests with coverage using the provided script
./test.sh

# Or run manually
pytest --cov=src/devops_mcps --cov-report=html --cov-report=xml tests/
```

**Test Script Features:**

The project includes a comprehensive `test.sh` script that:
- Automatically checks for `uv` installation
- Syncs development dependencies
- Runs all tests with pytest
- Generates both HTML and XML coverage reports
- Automatically opens the HTML coverage report in your browser
- Requires minimum 80% test coverage (currently achieving 93.77%)

**Coverage Reports:**
- HTML report: `coverage/html/index.html` (opens automatically)
- XML report: `coverage/coverage.xml` (for CI/CD integration)

**Debugging with MCP Inspector:**

```bash
# Basic run
npx @modelcontextprotocol/inspector uvx run devops-mcps

# Run with specific environment variables
npx @modelcontextprotocol/inspector uvx run devops-mcps -e GITHUB_PERSONAL_ACCESS_TOKEN=... -e JENKINS_URL=... # Add other vars
```

**Checking for package dependencies outdated**

```bash
uv pip list --outdated
```

**Updating package dependencies**
```bash
uv lock --upgrade
```

## CI/CD

A GitHub Actions workflow (`.github/workflows/ci.yml`) handles:

1.  **Linting & Testing**: Runs Ruff and Pytest on pushes and pull requests.
2.  **Publishing**: Builds and publishes the Python package to PyPI and the Docker image to Docker Hub on pushes to the `main` branch.

**Required Repository Secrets:**

-   `PYPI_API_TOKEN`: PyPI token for package publishing.
-   `DOCKER_HUB_USERNAME`: Docker Hub username.
-   `DOCKER_HUB_TOKEN`: Docker Hub access token.

## Packaging and Publishing (Manual)

Ensure you have `build` and `twine` installed:

```bash
pip install -U build twine
```

1.  **Update Version**: Increment the version number in `pyproject.toml`.
2.  **Build**: `python -m build`
3.  **Upload**: `twine upload dist/*` (Requires `~/.pypirc` configuration or token input).

## Appendix: GitHub Search Query Syntax

Leverage GitHub's powerful search syntax within the MCP tools:

**Repository Search (`gh_search_repositories`):**

-   `in:name,description,readme`: Search specific fields.
    *Example: `fastapi in:name`*
-   `user:USERNAME` or `org:ORGNAME`: Scope search to a user/org.
    *Example: `user:tiangolo fastapi`*
-   `language:LANGUAGE`: Filter by language.
    *Example: `http client language:python`*
-   `stars:>N`, `forks:<N`, `created:YYYY-MM-DD`, `pushed:>YYYY-MM-DD`: Filter by metrics and dates.
    *Example: `language:javascript stars:>1000 pushed:>2024-01-01`*
-   `topic:TOPIC-NAME`: Filter by topic.
    *Example: `topic:docker topic:python`*
-   `license:LICENSE-KEYWORD`: Filter by license (e.g., `mit`, `apache-2.0`).
    *Example: `language:go license:mit`*

**Code Search (`gh_search_code`):**

-   `in:file,path`: Search file content (default) or path.
    *Example: `"import requests" in:file`*
-   `repo:OWNER/REPO`: Scope search to a specific repository.
    *Example: `"JenkinsAPIException" repo:your-org/your-repo`*
-   `language:LANGUAGE`: Filter by file language.
    *Example: `def main language:python`*
-   `path:PATH/TO/DIR`, `filename:FILENAME.EXT`, `extension:EXT`: Filter by path, filename, or extension.
    *Example: `"GithubException" path:src/devops_mcps extension:py`*

**References:**

-   [Searching on GitHub](https://docs.github.com/en/search-github/searching-on-github)
-   [Searching Code](https://docs.github.com/en/search-github/searching-on-github/searching-code)
-   [Searching Repositories](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.