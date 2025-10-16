"""
Server assets resource management for dynamic capability listing.

Provides dynamic information about available prompts, tools, and resources
for the list_mcp_assets prompt functionality.
"""

from typing import Dict, Any, List
from datetime import datetime


class ServerAssetsResource:
    """Manages dynamic server capability information."""

    def __init__(self):
        self._last_updated = datetime.now().isoformat()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive server capabilities information."""
        return {
            "metadata": {
                "server_name": "Maven MCP Server",
                "version": "1.0.0",
                "last_updated": self._last_updated,
                "description": "Model Context Protocol server for Maven dependency management",
            },
            "prompts": self._get_prompt_info(),
            "tools": self._get_tool_info(),
            "resources": self._get_resource_info(),
            "quick_start": self._get_quick_start_info(),
        }

    def _get_prompt_info(self) -> List[Dict[str, Any]]:
        """Get information about available prompts."""
        return [
            {
                "name": "list_mcp_assets",
                "description": "Comprehensive overview of all server capabilities",
                "arguments": [],
                "usage": "Provides dynamic listing of prompts, tools, and resources with examples",
            },
            {
                "name": "triage",
                "description": "Analyze dependencies and create vulnerability triage report",
                "arguments": [
                    {
                        "name": "service_name",
                        "type": "str",
                        "required": True,
                        "description": "Name of the service to analyze",
                    },
                    {
                        "name": "workspace",
                        "type": "str",
                        "required": False,
                        "description": "Path to workspace (defaults to ./service_name)",
                    },
                ],
                "usage": "Comprehensive analysis following enterprise workflow: Discovery → Analysis → Security → Report",
            },
            {
                "name": "plan",
                "description": "Create actionable update plan from triage report",
                "arguments": [
                    {
                        "name": "service_name",
                        "type": "str",
                        "required": True,
                        "description": "Name of the service to plan updates for",
                    },
                    {
                        "name": "priorities",
                        "type": "List[str]",
                        "required": False,
                        "description": "Priority levels to include (defaults to ['CRITICAL', 'HIGH'])",
                    },
                ],
                "usage": "Creates structured remediation plan with phases, tasks, and full traceability to triage findings",
            },
        ]

    def _get_tool_info(self) -> List[Dict[str, Any]]:
        """Get information about available tools."""
        return [
            {
                "category": "Version Management",
                "tools": [
                    {
                        "name": "check_version_tool",
                        "description": "Check a Maven version and get all version update information",
                        "parameters": [
                            "dependency",
                            "version",
                            "packaging",
                            "classifier",
                        ],
                    },
                    {
                        "name": "check_version_batch_tool",
                        "description": "Process multiple Maven dependency version checks in a single batch",
                        "parameters": ["dependencies"],
                    },
                    {
                        "name": "list_available_versions_tool",
                        "description": "List all available versions grouped by minor version tracks",
                        "parameters": ["dependency", "version", "include_all_versions"],
                    },
                ],
            },
            {
                "category": "Security Scanning",
                "tools": [
                    {
                        "name": "scan_java_project_tool",
                        "description": "Scan Java Maven projects for vulnerabilities using Trivy",
                        "parameters": [
                            "workspace",
                            "scan_mode",
                            "severity_filter",
                            "max_results",
                        ],
                    },
                    {
                        "name": "analyze_pom_file_tool",
                        "description": "Analyze a single Maven POM file for dependencies and vulnerabilities",
                        "parameters": ["pom_file_path", "include_vulnerability_check"],
                    },
                ],
            },
        ]

    def _get_resource_info(self) -> List[Dict[str, Any]]:
        """Get information about available resources."""
        return [
            {
                "uri_pattern": "triage://reports/{service_name}/latest",
                "description": "Latest triage report for a service",
                "data_format": "TriageReport with metadata, vulnerabilities, and dependency updates",
                "usage": "Stores comprehensive triage analysis results for plan generation",
            },
            {
                "uri_pattern": "plans://updates/{service_name}/latest",
                "description": "Current update plan for a service",
                "data_format": "UpdatePlan with phases, tasks, and progress tracking",
                "usage": "Stores structured remediation plans with full traceability",
            },
            {
                "uri_pattern": "assets://server/capabilities",
                "description": "Dynamic list of server capabilities",
                "data_format": "Comprehensive capability information",
                "usage": "Used by list_mcp_assets prompt for dynamic content generation",
            },
        ]

    def _get_quick_start_info(self) -> Dict[str, Any]:
        """Get quick start workflow information."""
        return {
            "workflow_steps": [
                {
                    "step": 1,
                    "action": "Run triage",
                    "command": 'triage(service_name="my-service")',
                    "result": "Comprehensive analysis stored in triage://reports/my-service/latest",
                },
                {
                    "step": 2,
                    "action": "Review triage report",
                    "command": "Access triage://reports/my-service/latest",
                    "result": "Detailed vulnerability and dependency analysis",
                },
                {
                    "step": 3,
                    "action": "Create update plan",
                    "command": 'plan(service_name="my-service")',
                    "result": "Actionable plan stored in plans://updates/my-service/latest",
                },
                {
                    "step": 4,
                    "action": "Implement updates",
                    "command": "Use individual tools to execute specific updates",
                    "result": "Dependencies updated following structured plan",
                },
            ],
            "pro_tips": [
                "Triage reports are automatically stored and can be retrieved later",
                "Update plans track which changes have been applied",
                "Use scan_mode='pom_only' for large projects to avoid token limits",
                "All plan tasks include full traceability back to triage findings",
            ],
        }
