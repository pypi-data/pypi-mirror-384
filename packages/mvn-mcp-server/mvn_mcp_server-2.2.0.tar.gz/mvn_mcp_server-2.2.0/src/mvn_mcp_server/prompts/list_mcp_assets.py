"""
List MCP Assets prompt for comprehensive server capability overview.

Provides dynamic listing of all available prompts, tools, and resources
with usage examples and quick start guidance.
"""

from typing import List, Dict, Any

# Define Message type for development/testing
Message = Dict[str, Any]


async def list_mcp_assets() -> List[Message]:
    """Return a comprehensive list of all MCP server capabilities."""

    content = """# 🚀 Maven MCP Server Assets

## 📝 Prompts
Interactive conversation starters and guided workflows:

• **list_mcp_assets** () - Comprehensive overview of all server capabilities
• **triage** (service_name, workspace) - Analyze dependencies and vulnerabilities
• **plan** (service_name, priorities) - Create actionable update plan from triage

## 🔧 Tools
Maven dependency management and analysis functions:

### Version Management
• **check_version_tool** (dependency, version, packaging, classifier) - Check version and get update info
• **check_version_batch_tool** (dependencies) - Process multiple version checks efficiently
• **list_available_versions_tool** (dependency, version, include_all_versions) - List versions by tracks

### Security Scanning
• **scan_java_project_tool** (workspace, scan_mode, severity_filter, max_results) - Scan for vulnerabilities
• **analyze_pom_file_tool** (pom_file_path, include_vulnerability_check) - Analyze single POM file

## 📂 Resources
Dynamic data and persistent state:

• **triage://reports/{service_name}/latest** - Latest triage report for a service
• **plans://updates/{service_name}/latest** - Current update plan for a service
• **assets://server/capabilities** - Dynamic server capabilities list

---

## 🎯 Quick Start Workflow

### Enterprise Dependency Management Pattern

1. **Analyze Dependencies**
   ```
   Use prompt: triage
   Arguments: service_name="my-service", workspace="./my-service"
   Result: Comprehensive analysis stored in triage://reports/my-service/latest
   ```

2. **Review Triage Report**
   ```
   Access resource: triage://reports/my-service/latest
   Contains: Vulnerabilities, outdated dependencies, POM analysis, recommendations
   ```

3. **Create Update Plan**
   ```
   Use prompt: plan
   Arguments: service_name="my-service", priorities=["CRITICAL", "HIGH"]
   Result: Actionable plan stored in plans://updates/my-service/latest
   ```

4. **Execute Updates**
   ```
   Use individual tools to implement specific updates following the plan:
   - check_version_tool for validation
   - scan_java_project_tool for verification
   ```

---

## 💡 Pro Tips

### Workflow Optimization
• **Triage First**: Always start with triage for comprehensive analysis
• **Resource Persistence**: Triage reports and plans are automatically stored and retrievable
• **Batch Processing**: Use check_version_batch_tool for multiple dependencies
• **Scan Modes**: Use scan_mode="pom_only" for large projects to avoid token limits

### Traceability
• **Full Audit Trail**: Every plan task links back to specific triage findings
• **CVE Tracking**: Plans include specific CVE IDs and remediation guidance
• **Progress Tracking**: Plans track implementation status and completion

### Best Practices
• **Phase-Based Updates**: Follow plan phases (Critical → High → Medium → Low)
• **Verification Steps**: Each phase includes verification using security scanning
• **Documentation**: Plans include specific file locations and change instructions

---

## 🔄 Workflow Example

```bash
# 1. Start comprehensive triage analysis
Use prompt: triage with service_name="user-service"

# 2. Review findings (stored automatically)
Access: triage://reports/user-service/latest

# 3. Generate focused update plan
Use prompt: plan with service_name="user-service", priorities=["CRITICAL"]

# 4. Implement critical security updates
Follow plan tasks with full traceability to CVE findings

# 5. Verify security improvements
Use tool: scan_java_project_tool to confirm vulnerabilities resolved
```

---

## 📊 Resource Data Formats

### Triage Reports
```json
{
  "metadata": {
    "report_id": "service-triage-2024-01-24",
    "service_name": "user-service",
    "vulnerability_counts": {"critical": 2, "high": 5, "medium": 8}
  },
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-1234",
      "severity": "CRITICAL",
      "dependency": "log4j-core",
      "current_version": "2.14.1",
      "fix_version": "2.17.1"
    }
  ],
  "dependency_updates": [...]
}
```

### Update Plans
```json
{
  "metadata": {
    "plan_id": "service-plan-2024-01-24",
    "triage_report_id": "service-triage-2024-01-24",
    "total_updates": 15
  },
  "phases": [
    {
      "phase_name": "Critical Security Updates",
      "priority": "CRITICAL",
      "tasks": [
        {
          "dependency": "log4j-core",
          "current_version": "2.14.1",
          "target_version": "2.17.1",
          "traceability_link": "CVE-2024-1234",
          "file_location": "parent-pom.xml"
        }
      ]
    }
  ]
}
```

---

**🚀 Ready to get started? Begin with `triage` to analyze your service dependencies!**"""

    return [{"role": "user", "content": content}]
