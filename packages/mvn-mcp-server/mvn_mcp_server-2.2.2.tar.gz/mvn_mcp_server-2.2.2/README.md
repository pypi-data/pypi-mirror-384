# Maven MCP Server

[![CI](https://github.com/danielscholl/mvn-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/danielscholl/mvn-mcp-server/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/danielscholl/mvn-mcp-server)](https://github.com/danielscholl/mvn-mcp-server/releases)
[![Python](https://img.shields.io/badge/python-3.12%20|%203.13-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green)](https://modelcontextprotocol.io)

**AI-powered Maven dependency management through natural language.**

Maven MCP Server enables AI assistants to interact with Maven Central repository, providing comprehensive tools for version checking, security scanning, and dependency analysis—all through conversational interfaces.

## Why Maven MCP Server?

**Traditional Maven workflow:**
```bash
mvn versions:display-dependency-updates  # Check all dependencies
# Read through XML output, manually check each update
# Manually verify security advisories
# Repeat for each project...
```

**With Maven MCP Server:**
```
You: "Scan this project for vulnerabilities and create an update plan"
AI: ✅ Found 3 critical CVEs, 12 outdated dependencies
    📋 Created prioritized update plan with file locations
    🎯 Ready to implement
```

> **Key Benefits:**
> - Natural language instead of complex Maven commands
> - Single workflow combining version checks + security + planning
> - AI-assisted decision making with full context
> - Intelligent caching for faster repeated queries
> - Enterprise-ready with audit trails and traceability

## Features

| Category | Capabilities |
|----------|-------------|
| **Version Management** | Check single or batch dependency versions • Discover available updates (major/minor/patch) • List version history grouped by tracks |
| **Security Scanning** | Integrate Trivy vulnerability scanning • CVE detection with severity filtering • Multi-module project support • Profile-based scanning for multi-cloud deployments |
| **Enterprise Workflows** | Guided dependency triage analysis • Actionable remediation planning • Complete audit trail with CVE traceability |
| **AI-Optimized** | Single-call comprehensive responses • Batch operations for efficiency • Intelligent caching |

## Quick Start

**Prerequisites:**

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [trivy](https://trivy.dev) (optional, for security scanning)
- [maven](https://maven.apache.org/install.html) (optional, for profile-based scanning)


### Setup

[![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-UV-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode:mcp/install?%7B%22name%22%3A%22mvn-mcp-server%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mvn-mcp-server%22%5D%2C%22env%22%3A%7B%7D%7D)


```bash
mcp add mvn-mcp-server -- uvx mvn-mcp-server
```

Or add manually to your MCP configuration:

```json
{
  "mcpServers": {
    "mvn-mcp-server": {
      "command": "uvx",
      "args": ["mvn-mcp-server"]
    }
  }
}
```


### Try It

> "Check if Spring Core 5.3.0 has any updates available"

> "Scan my Java project for security vulnerabilities"


### Optional: Security Scanning

Install **Trivy** for vulnerability detection:

```bash
# macOS
brew install trivy

# Linux
# See: https://aquasecurity.github.io/trivy/latest/getting-started/installation/
```

Without Trivy, version checking and dependency analysis work normally. Security scanning tools will gracefully report Trivy unavailable.

**Security Note:** All processing happens locally. No source code or project data is sent to external services (except public Maven Central API queries for version information).

## Available Tools

| Tool | Description | Example Query |
|------|-------------|---------------|
| **check_version_tool** | Check single dependency version | `Check org.springframework:spring-core version 5.3.0` |
| **check_version_batch_tool** | Check multiple dependencies | `Check these for updates: spring-core 5.3.0, junit 4.13.2` |
| **list_available_versions_tool** | List version history by tracks | `Show all versions of commons-lang3` |
| **scan_java_project_tool** | Security scan with Trivy | `Scan this project for vulnerabilities` |
| **analyze_pom_file_tool** | Analyze POM file | `Analyze this pom.xml for issues` |

## Available Prompts

| Prompt | Description | Example Query |
|--------|-------------|---------------|
| **list_mcp_assets_prompt** | Show all capabilities with examples | `What can this server do?` |
| **triage** | Complete dependency and vulnerability analysis | `Run triage for my-service` |
| **plan** | Generate actionable remediation plan | `Create update plan for my-service` |

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**[Usage](https://github.com/danielscholl/mvn-mcp-server/blob/main/docs/project-usage.md)** • **[Architecture](https://github.com/danielscholl/mvn-mcp-server/blob/main/docs/project-architect.md)** • **[Contributing](https://github.com/danielscholl/mvn-mcp-server/blob/main/CONTRIBUTING.md)**

</div>
