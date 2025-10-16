"""mvn MCP Server using FastMCP framework.

This module creates and configures the FastMCP server instance for the Maven MCP tools.
"""

import logging
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# Import the consolidated tools
from mvn_mcp_server.tools.check_version import check_version
from mvn_mcp_server.tools.check_version_batch import check_version_batch
from mvn_mcp_server.tools.list_available_versions import list_available_versions
from mvn_mcp_server.tools.java_security_scan import scan_java_project
from mvn_mcp_server.tools.analyze_pom_file import analyze_pom_file

# Import prompts
from mvn_mcp_server.prompts.list_mcp_assets import list_mcp_assets
from mvn_mcp_server.prompts.triage import dependency_triage
from mvn_mcp_server.prompts.plan import update_plan

# Import resources
from mvn_mcp_server.resources.triage_reports import TriageReportResource
from mvn_mcp_server.resources.update_plans import UpdatePlanResource
from mvn_mcp_server.resources.server_assets import ServerAssetsResource

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mvn-mcp-server")

# Create FastMCP server instance
mcp = FastMCP(
    name="mvn MCP Server",
    instructions="""
        This server provides comprehensive Maven dependency management tools.
        Use check_version_tool() for single dependency analysis.
        Use check_version_batch_tool() for multiple dependencies.
        Use scan_java_project_tool() for security vulnerability scanning.
        Use triage and plan prompts for enterprise workflows.
    """,
)

# Initialize resource instances
triage_resource = TriageReportResource()
plan_resource = UpdatePlanResource()
assets_resource = ServerAssetsResource()


# Register prompts
@mcp.prompt()
async def list_mcp_assets_prompt():
    """Return a comprehensive list of all MCP server capabilities."""
    logger.info("MCP prompt: list_mcp_assets")
    return await list_mcp_assets()


@mcp.prompt()
async def triage(service_name: str, workspace: Optional[str] = None):
    """Analyze service dependencies and create vulnerability triage report."""
    logger.info(f"MCP prompt: triage for service {service_name}")
    return await dependency_triage(service_name, workspace)


@mcp.prompt()
async def plan(service_name: str, priorities: Optional[List[str]] = None):
    """Create actionable update plan based on triage report."""
    logger.info(f"MCP prompt: plan for service {service_name}")
    return await update_plan(service_name, priorities)


# Register resources
@mcp.resource("triage://reports/{service_name}/latest")
async def get_triage_report(service_name: str):
    """Get the latest triage report for a service."""
    logger.info(f"MCP resource: retrieving triage report for {service_name}")
    report_data = await triage_resource.get_report_data(service_name)
    if not report_data:
        return {"error": f"No triage report found for {service_name}"}
    return report_data


@mcp.resource("plans://updates/{service_name}/latest")
async def get_update_plan(service_name: str):
    """Get the current update plan for a service."""
    logger.info(f"MCP resource: retrieving update plan for {service_name}")
    plan_data = await plan_resource.get_plan_data(service_name)
    if not plan_data:
        return {"error": f"No update plan found for {service_name}"}
    return plan_data


@mcp.resource("assets://server/capabilities")
async def get_server_capabilities():
    """Get dynamic list of server capabilities."""
    logger.info("MCP resource: retrieving server capabilities")
    return assets_resource.get_capabilities()


# Register new consolidated tools


@mcp.tool(
    description="Check a Maven version and get all version update information in a single call"
)
def check_version_tool(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: Optional[str] = None,
):
    """Check a Maven dependency version and provide comprehensive version information.

    This consolidated tool checks if a version exists and simultaneously provides
    information about the latest available versions across all semantic versioning components.

    Args:
        dependency: Maven dependency in groupId:artifactId format
        version: Version string to check and use as reference
        packaging: Package type (jar, war, etc.), defaults to "jar"
        classifier: Optional classifier

    Returns:
        Comprehensive version information including:
        - If the version exists
        - The latest versions available (major, minor, patch)
        - Which updates are available
    """
    logger.info(f"MCP call to consolidated check_version with: {dependency}, {version}")
    result = check_version(dependency, version, packaging, classifier)
    logger.info(
        f"Result summary: {dependency} v{version} exists={result.get('result', {}).get('exists', False)}"
    )
    return result


@mcp.tool(
    description="Process multiple Maven dependency version checks in a single batch request"
)
def check_version_batch_tool(dependencies: List[Dict[str, Any]]):
    """Process multiple Maven dependency version checks in a single batch request.

    This tool efficiently handles processing multiple dependencies in a single call,
    reducing the number of API calls and providing a summary of updates available.

    Args:
        dependencies: List of dependency objects, each containing:
            - dependency: Maven dependency in groupId:artifactId format
            - version: Version string to check and use as reference
            - packaging: (Optional) Package type, defaults to "jar"
            - classifier: (Optional) Classifier

    Returns:
        Comprehensive batch results including:
        - Summary statistics (total, success, failed, updates available)
        - Detailed information for each dependency
    """
    logger.info(
        f"MCP call to batch check_version with {len(dependencies)} dependencies"
    )
    result = check_version_batch(dependencies)
    summary = result.get("result", {}).get("summary", {})
    logger.info(
        f"Batch result summary: {summary.get('success', 0)}/{summary.get('total', 0)} successful, "
        f"updates available: major={summary.get('updates_available', {}).get('major', 0)}, "
        f"minor={summary.get('updates_available', {}).get('minor', 0)}, "
        f"patch={summary.get('updates_available', {}).get('patch', 0)}"
    )
    return result


@mcp.tool(
    description="List all available versions of a Maven artifact grouped by minor version tracks"
)
def list_available_versions_tool(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: Optional[str] = None,
    include_all_versions: bool = False,
):
    """List all available versions of a Maven dependency grouped by minor tracks.

    This tool provides a comprehensive view of all available versions for a Maven dependency,
    organized by major.minor version tracks. It helps developers make informed decisions
    about version upgrades by showing the complete version landscape.

    Args:
        dependency: Maven dependency in groupId:artifactId format
        version: Current version string to use as reference
        packaging: Package type (jar, war, etc.), defaults to "jar"
        classifier: Optional classifier
        include_all_versions: Whether to include all versions in the response (default: False)
            When False, only includes versions for the current track
            When True, includes full version lists for all tracks

    Returns:
        Structured version information including:
        - Current version and whether it exists
        - Latest overall version
        - All minor version tracks with their latest versions
        - Full version lists for selected tracks based on include_all_versions
    """
    logger.info(
        f"MCP call to list_available_versions with: {dependency}, {version}, include_all={include_all_versions}"
    )
    result = list_available_versions(
        dependency, version, packaging, classifier, include_all_versions
    )

    # Log info about the result
    minor_tracks = result.get("result", {}).get("minor_tracks", {})
    track_count = len(minor_tracks)
    current_track = next(
        (
            track
            for track, info in minor_tracks.items()
            if info.get("is_current_track", False)
        ),
        "none",
    )

    logger.info(
        f"Found {track_count} minor version tracks for {dependency}, "
        f"current track: {current_track}"
    )

    return result


@mcp.tool(
    description="Java-specific tool for scanning Maven projects for vulnerabilities"
)
def scan_java_project_tool(
    workspace: str,
    include_profiles: Optional[List[str]] = None,
    scan_all_modules: bool = True,
    scan_mode: str = "workspace",
    pom_file: Optional[str] = None,
    severity_filter: Optional[List[str]] = None,
    max_results: int = 100,
    offset: int = 0,
):
    """Scan a Java project for vulnerabilities and provide detailed security information.

    This tool performs comprehensive security scanning for Java Maven projects using
    Trivy vulnerability scanner. It supports various scanning modes and result filtering
    to manage token limits for large projects.

    Args:
        workspace: Absolute path to the Java project directory
        include_profiles: Optional list of Maven profiles to activate during scan
        scan_all_modules: Whether to scan all modules or just the specified project
        scan_mode: Scan mode, either "workspace" (scan entire directory) or "pom_only" (scan specific pom.xml)
        pom_file: Path to specific pom.xml file to scan (only used in "pom_only" mode)
        severity_filter: Optional list of severity levels to include (critical, high, medium, low)
        max_results: Maximum number of vulnerability results to return (default: 100)
        offset: Starting offset for paginated results (default: 0)

    Returns:
        Comprehensive vulnerability report including:
        - Detected vulnerabilities with severity levels
        - Module and profile-specific information
        - Remediation recommendations
        - Detailed dependency information
        - Pagination information
    """
    logger.info(f"MCP call to scan_java_project with workspace: {workspace}")
    logger.info(f"Scan mode: {scan_mode}")
    logger.info(f"Target POM file: {pom_file if pom_file else 'default'}")
    logger.info(f"Profiles to activate: {include_profiles}")
    logger.info(f"Scan all modules: {scan_all_modules}")
    logger.info(f"Severity filter: {severity_filter}")
    logger.info(f"Pagination: offset={offset}, max_results={max_results}")

    result = scan_java_project(
        workspace,
        include_profiles,
        scan_all_modules,
        scan_mode,
        pom_file,
        severity_filter,
        max_results,
        offset,
    )

    if result.get("status") == "success":
        vuln_found = result.get("result", {}).get("vulnerabilities_found", False)
        total = result.get("result", {}).get("total_vulnerabilities", 0)
        scan_mode = result.get("result", {}).get("scan_mode", "unknown")
        severity_counts = result.get("result", {}).get("severity_counts", {})

        logger.info(f"Java security scan completed in {scan_mode} mode.")
        logger.info(f"Vulnerabilities found: {vuln_found}, total: {total}")
        logger.info(
            f"Severity breakdown: critical={severity_counts.get('critical', 0)}, "
            f"high={severity_counts.get('high', 0)}, "
            f"medium={severity_counts.get('medium', 0)}, "
            f"low={severity_counts.get('low', 0)}"
        )
    else:
        error_code = result.get("error", {}).get("code", "unknown")
        error_msg = result.get("error", {}).get("message", "Unknown error")
        logger.error(
            f"Java security scan failed with error: {error_code} - {error_msg}"
        )

    return result


@mcp.tool(
    description="Analyze a single Maven POM file without scanning the entire workspace"
)
def analyze_pom_file_tool(pom_file_path: str, include_vulnerability_check: bool = True):
    """Analyze a Maven POM file for dependencies and potential vulnerabilities.

    This focused tool analyzes a single POM file without requiring the entire workspace structure,
    avoiding token limit issues that can occur with large multi-module Maven projects.

    Args:
        pom_file_path: Absolute path to the POM file to analyze
        include_vulnerability_check: Whether to check for known vulnerabilities (default: True)

    Returns:
        Comprehensive analysis of the POM file including:
        - Basic project information
        - Dependency counts and details
        - Parent POM relationship
        - Property references
        - Profile information
        - Known vulnerable dependencies (if vulnerability checking is enabled)
    """
    logger.info(f"MCP call to analyze_pom_file with: {pom_file_path}")
    logger.info(f"Include vulnerability check: {include_vulnerability_check}")

    result = analyze_pom_file(pom_file_path, include_vulnerability_check)

    if result.get("status") == "success":
        dependency_count = result.get("result", {}).get("dependency_count", 0)
        vulnerable_count = len(
            result.get("result", {}).get("known_vulnerable_dependencies", [])
        )

        logger.info(f"POM analysis completed for {pom_file_path}")
        logger.info(
            f"Found {dependency_count} dependencies, {vulnerable_count} with known vulnerabilities"
        )
    else:
        error_code = result.get("error", {}).get("code", "unknown")
        error_msg = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"POM analysis failed with error: {error_code} - {error_msg}")

    return result
