"""Java security scanning tool for Maven projects.

This module implements security scanning for Java projects using Trivy.
Supports profile-based scanning using Maven effective POMs.
"""

import os
import subprocess
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict

from fastmcp.exceptions import ValidationError, ToolError, ResourceError

from mvn_mcp_server.shared.data_types import (
    ErrorCode,
    JavaVulnerability,
    JavaSecurityScanResult,
    JavaPaginationInfo,
    ProfileScanResult,
    ProfileSpecificAnalysis,
)
from mvn_mcp_server.services.response import (
    format_success_response,
    format_error_response,
)
from mvn_mcp_server.services.maven_effective_pom import MavenEffectivePomService

# Set up logging
logger = logging.getLogger("mvn-mcp-server")


def check_trivy_availability() -> bool:
    """Check if Trivy is available on the system.

    Returns:
        bool: True if Trivy is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["trivy", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        return result.returncode == 0
    except FileNotFoundError:
        logger.warning("Trivy not found on the system.")
        return False


def _validate_scan_inputs(
    workspace: str,
    scan_mode: str,
    pom_file: Optional[str],
    severity_filter: Optional[List[str]],
) -> tuple[Path, Path, str, List[str]]:
    """Validate and prepare scan inputs.

    Returns:
        tuple: (workspace_path, target_path, scan_mode_desc, severity_filter)
    """
    # Validate workspace path
    workspace_path = Path(workspace)
    if not workspace_path.exists():
        raise ValidationError(f"Workspace directory does not exist: {workspace}")
    if not workspace_path.is_dir():
        raise ValidationError(f"Workspace path is not a directory: {workspace}")

    # Validate scan_mode parameter
    valid_scan_modes = ["workspace", "pom_only"]
    if scan_mode not in valid_scan_modes:
        raise ValidationError(
            f"Invalid scan_mode: {scan_mode}. Must be one of {valid_scan_modes}"
        )

    # Set default severity filter if none provided
    if severity_filter is None:
        severity_filter = ["critical", "high", "medium", "low", "unknown"]
    else:
        _validate_severity_filter(severity_filter)

    # Determine target path based on scan_mode
    if scan_mode == "pom_only":
        target_path = Path(pom_file) if pom_file else workspace_path / "pom.xml"
        if not target_path.exists():
            raise ValidationError(f"POM file does not exist: {target_path}")
        scan_mode_desc = "trivy-pom-only"
    else:
        pom_path = workspace_path / "pom.xml"
        if not pom_path.exists():
            raise ValidationError(
                f"Not a Maven project - no pom.xml found in {workspace}"
            )
        target_path = workspace_path
        scan_mode_desc = "trivy"

    return workspace_path, target_path, scan_mode_desc, severity_filter


def _validate_severity_filter(severity_filter: List[str]) -> None:
    """Validate severity filter values."""
    valid_severities = ["critical", "high", "medium", "low", "unknown"]
    for severity in severity_filter:
        if severity.lower() not in valid_severities:
            raise ValidationError(
                f"Invalid severity: {severity}. Must be one of {valid_severities}"
            )


def _run_trivy_scan(target_path: Path) -> Dict[str, Any]:
    """Run Trivy scan and return parsed results."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        output_file = temp_file.name

        trivy_cmd = [
            "trivy",
            "fs",
            "--security-checks",
            "vuln",
            "--format",
            "json",
            "--output",
            output_file,
            str(target_path),
        ]

        logger.info(f"Running Trivy command: {' '.join(trivy_cmd)}")
        result = subprocess.run(
            trivy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(f"Trivy scan failed: {result.stderr}")
            raise ResourceError(f"Trivy scan failed: {result.stderr}")

        try:
            with open(output_file, "r") as f:
                trivy_data = json.load(f)
            return trivy_data
        except Exception as e:
            raise ToolError(f"Error processing Trivy results: {str(e)}")
        finally:
            os.unlink(output_file)


def _process_trivy_results(
    trivy_data: Dict[str, Any], severity_filter: List[str]
) -> List[JavaVulnerability]:
    """Process Trivy scan results into vulnerability records."""
    all_results = []

    for result in trivy_data.get("Results", []):
        target_file = result.get("Target", "unknown")

        for vuln in result.get("Vulnerabilities", []):
            vuln_record = _create_vulnerability_record(
                vuln, target_file, severity_filter
            )
            if vuln_record:
                all_results.append(vuln_record)

    return all_results


def _create_vulnerability_record(
    vuln: Dict[str, Any], target_file: str, severity_filter: List[str]
) -> Optional[JavaVulnerability]:
    """Create a vulnerability record from Trivy vulnerability data."""
    pkg_id = vuln.get("PkgID", "")
    pkg_parts = pkg_id.split(":")

    if len(pkg_parts) < 3:
        return None

    group_id = pkg_parts[0]
    artifact_id = pkg_parts[1]
    installed_version = pkg_parts[2]

    vuln_severity = vuln.get("Severity", "unknown").lower()

    # Skip if not in the severity filter
    if vuln_severity not in [s.lower() for s in severity_filter]:
        return None

    vuln_record = JavaVulnerability(
        module="main",
        group_id=group_id,
        artifact_id=artifact_id,
        installed_version=installed_version,
        vulnerability_id=vuln.get("VulnerabilityID", "unknown"),
        cve_id=vuln.get("VulnerabilityID", ""),
        severity=vuln_severity,
        description=vuln.get("Description", "No description available"),
        recommendation=vuln.get("FixedVersion", "Upgrade recommended"),
        in_profile=None,
        direct_dependency=True,
        is_in_bom=False,
        version_source="direct",
        source_location=target_file,
        links=[
            ref.get("URL", "") for ref in vuln.get("References", []) if "URL" in ref
        ],
        fix_available=bool(vuln.get("FixedVersion", "")),
    )

    return vuln_record


def _calculate_severity_counts(
    vulnerabilities: List[JavaVulnerability],
) -> Dict[str, int]:
    """Calculate severity counts from vulnerability results."""
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}

    for vulnerability in vulnerabilities:
        severity = vulnerability.severity.lower()
        if severity in severity_counts:
            severity_counts[severity] += 1

    return severity_counts


def _apply_pagination(
    all_results: List[JavaVulnerability], offset: int, max_results: int
) -> tuple[List[JavaVulnerability], JavaPaginationInfo]:
    """Apply pagination to results and return paginated data with pagination info."""
    total_vulnerabilities = len(all_results)

    # Validate offset
    if offset < 0:
        offset = 0
    if offset > total_vulnerabilities:
        offset = max(0, total_vulnerabilities - max_results)

    # Apply pagination
    scan_results = all_results[offset : offset + max_results]

    # Calculate pagination info
    has_more = (offset + max_results) < total_vulnerabilities

    pagination_info = JavaPaginationInfo(
        offset=offset,
        max_results=max_results,
        total_results=total_vulnerabilities,
        has_more=has_more,
    )

    return scan_results, pagination_info


def _handle_scan_error(e: Exception, tool_name: str) -> Dict[str, Any]:
    """Handle and format scan errors."""
    if isinstance(e, ValidationError):
        logger.error(f"Validation error: {str(e)}")
        return format_error_response(tool_name, ErrorCode.INVALID_INPUT_FORMAT, str(e))
    elif isinstance(e, ResourceError):
        logger.error(f"Resource error: {str(e)}")
        error_code = (
            ErrorCode.MAVEN_ERROR
            if "maven" in str(e).lower()
            else ErrorCode.TRIVY_ERROR
        )
        return format_error_response(tool_name, error_code, str(e))
    else:
        logger.error(f"Unexpected error in Java security scan: {str(e)}")
        error_code = _determine_error_code(e)
        return format_error_response(
            tool_name, error_code, f"Error in Java security scan: {str(e)}"
        )


def _determine_error_code(e: Exception) -> ErrorCode:
    """Determine the appropriate error code for an exception."""
    if isinstance(e, FileNotFoundError):
        return ErrorCode.DIRECTORY_NOT_FOUND
    elif "pom.xml" in str(e):
        return ErrorCode.NOT_MAVEN_PROJECT
    elif "mvn" in str(e) or "maven" in str(e).lower():
        return ErrorCode.MAVEN_ERROR
    elif "trivy" in str(e).lower():
        return ErrorCode.TRIVY_ERROR
    else:
        return ErrorCode.INTERNAL_SERVER_ERROR


def _analyze_profile_specificity(
    profile_results: Dict[str, Dict[str, Any]],
) -> ProfileSpecificAnalysis:
    """Analyze which vulnerabilities are common vs. profile-specific.

    Args:
        profile_results: Dict mapping profile_id to scan results

    Returns:
        ProfileSpecificAnalysis with common and profile-specific CVEs
    """
    # Map CVE IDs to the profiles where they appear
    cve_to_profiles = defaultdict(set)

    for profile_id, results in profile_results.items():
        for vuln in results["vulnerabilities"]:
            cve_id = vuln.cve_id if hasattr(vuln, "cve_id") else ""
            if cve_id:
                cve_to_profiles[cve_id].add(profile_id)

    # Identify CVEs common to all profiles
    all_profiles = set(profile_results.keys())
    common_cves = [
        cve_id
        for cve_id, profiles in cve_to_profiles.items()
        if profiles == all_profiles
    ]

    # Identify profile-specific CVEs (unique to one profile)
    profile_specific = {}
    for profile_id in profile_results.keys():
        specific_cves = [
            cve_id
            for cve_id, profiles in cve_to_profiles.items()
            if profiles == {profile_id}
        ]
        if specific_cves:
            profile_specific[f"{profile_id}_only"] = specific_cves

    return ProfileSpecificAnalysis(
        common_to_all_profiles=common_cves, profile_specific_cves=profile_specific
    )


def _aggregate_profile_results(
    profile_results: Dict[str, Dict[str, Any]], max_results: int, offset: int
) -> Dict[str, Any]:
    """Aggregate results from multiple profile scans.

    Args:
        profile_results: Dict mapping profile_id to scan results
        max_results: Maximum results to return
        offset: Pagination offset

    Returns:
        Aggregated scan results with per-profile breakdown
    """
    # Combine all vulnerabilities from all profiles
    all_vulnerabilities = []
    for profile_id, results in profile_results.items():
        all_vulnerabilities.extend(results["vulnerabilities"])

    # Calculate aggregated severity counts
    aggregated_severity_counts = _calculate_severity_counts(all_vulnerabilities)

    # Apply pagination to aggregated results
    paginated_vulns, pagination_info = _apply_pagination(
        all_vulnerabilities, offset, max_results
    )

    # Cross-profile analysis
    profile_specificity = _analyze_profile_specificity(profile_results)

    # Convert profile results to Pydantic models for response
    per_profile_pydantic = {}
    for profile_id, results in profile_results.items():
        per_profile_pydantic[profile_id] = ProfileScanResult(
            profile_id=profile_id,
            effective_pom_used=True,
            vulnerabilities_found=results["total_vulnerabilities"] > 0,
            total_vulnerabilities=results["total_vulnerabilities"],
            severity_counts=results["severity_counts"],
            vulnerabilities=results["vulnerabilities"],
        ).model_dump()

    return {
        "scan_mode": "profile-effective",
        "vulnerabilities_found": len(all_vulnerabilities) > 0,
        "total_vulnerabilities": len(all_vulnerabilities),
        "modules_scanned": list(profile_results.keys()),
        "profiles_activated": list(profile_results.keys()),
        "severity_counts": aggregated_severity_counts,
        "vulnerabilities": paginated_vulns,
        "pagination": pagination_info,
        "scan_limitations": None,
        "recommendations": None,
        "per_profile_results": per_profile_pydantic,
        "profile_specific_vulnerabilities": profile_specificity,
        "maven_available": True,
    }


def _scan_with_profiles(
    workspace_path: Path,
    profiles: List[str],
    severity_filter: List[str],
    max_results: int,
    offset: int,
) -> Dict[str, Any]:
    """Execute profile-based scanning using Maven effective POMs.

    Args:
        workspace_path: Path to the Maven project
        profiles: List of profile IDs to scan
        severity_filter: Severity levels to include
        max_results: Maximum results to return
        offset: Pagination offset

    Returns:
        Aggregated profile scan results

    Raises:
        ResourceError: If Maven or Trivy operations fail
    """
    logger.info(f"Starting profile-based scanning for profiles: {profiles}")

    # Generate effective POMs for each profile
    effective_poms = MavenEffectivePomService.generate_effective_poms_for_profiles(
        workspace_path, profiles
    )

    try:
        # Scan each effective POM
        profile_results = {}

        for profile_id, effective_pom_path in effective_poms.items():
            logger.info(f"Scanning effective POM for profile: {profile_id}")

            # Run Trivy scan on effective POM
            trivy_data = _run_trivy_scan(effective_pom_path)

            # Process results
            vulnerabilities = _process_trivy_results(trivy_data, severity_filter)

            # Tag vulnerabilities with profile
            for vuln in vulnerabilities:
                vuln.in_profile = profile_id

            # Calculate severity counts for this profile
            severity_counts = _calculate_severity_counts(vulnerabilities)

            # Store profile results
            profile_results[profile_id] = {
                "vulnerabilities": vulnerabilities,
                "total_vulnerabilities": len(vulnerabilities),
                "severity_counts": severity_counts,
            }

            logger.info(
                f"Profile {profile_id}: found {len(vulnerabilities)} vulnerabilities"
            )

        # Aggregate results from all profiles
        aggregated_results = _aggregate_profile_results(
            profile_results, max_results, offset
        )

        return aggregated_results

    finally:
        # Always cleanup temporary effective POMs
        MavenEffectivePomService.cleanup_effective_poms(effective_poms)
        logger.info("Cleaned up temporary effective POM files")


def scan_java_project(
    workspace: str,
    include_profiles: Optional[List[str]] = None,
    scan_all_modules: bool = True,
    scan_mode: str = "workspace",
    pom_file: Optional[str] = None,
    severity_filter: Optional[List[str]] = None,
    max_results: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Scan a Java project for vulnerabilities using Trivy.

    Args:
        workspace: Absolute path to the Java project directory
        include_profiles: List of Maven profiles to activate during scan
        scan_all_modules: Whether to scan all modules or just the specified project
        scan_mode: Scan mode, either "workspace" (scan entire directory) or "pom_only" (scan specific pom.xml)
        pom_file: Path to specific pom.xml file to scan (only used in "pom_only" mode)
        severity_filter: Optional list of severity levels to include (critical, high, medium, low)
        max_results: Maximum number of vulnerability results to return (default: 100)
        offset: Starting offset for paginated results (default: 0)

    Returns:
        Dict containing the scan results with vulnerability information

    Raises:
        ValidationError: If input parameters are invalid or directory doesn't exist
        ResourceError: If there's an issue with scanning tools or Maven
        ToolError: For other unexpected errors
    """
    tool_name = "scan_java_project"

    try:
        # Set default profiles if none provided
        if include_profiles is None:
            include_profiles = []

        # Validate inputs and prepare scan parameters
        workspace_path, target_path, scan_mode_desc, severity_filter = (
            _validate_scan_inputs(workspace, scan_mode, pom_file, severity_filter)
        )

        # Check Trivy availability
        if not check_trivy_availability():
            raise ResourceError(
                "Trivy is not available. Please install Trivy to perform security scanning."
            )

        # Log scan parameters
        logger.info(f"Starting Java security scan for {workspace}")
        logger.info(f"Scan mode: {scan_mode}, Target: {target_path}")
        logger.info(f"Profiles: {include_profiles}, Severity filter: {severity_filter}")
        logger.info(f"Pagination: offset={offset}, max_results={max_results}")

        # Determine if profile-based scanning should be used
        maven_available = MavenEffectivePomService.check_maven_availability()
        use_profile_scanning = include_profiles and maven_available

        if use_profile_scanning:
            # Use profile-based scanning with effective POMs
            logger.info(
                f"Using profile-based scanning for profiles: {include_profiles}"
            )
            result_data = _scan_with_profiles(
                workspace_path, include_profiles, severity_filter, max_results, offset
            )

            # Create scan result from aggregated data
            scan_result = JavaSecurityScanResult(**result_data)

        else:
            # Use standard workspace scanning
            if include_profiles and not maven_available:
                logger.warning(
                    "Profiles specified but Maven not available - using workspace scan"
                )

            # Run Trivy scan
            trivy_data = _run_trivy_scan(target_path)

            # Process scan results
            all_results = _process_trivy_results(trivy_data, severity_filter)

            # Calculate severity counts
            severity_counts = _calculate_severity_counts(all_results)

            # Apply pagination
            scan_results, pagination_info = _apply_pagination(
                all_results, offset, max_results
            )

            # Log results
            total_vulnerabilities = len(all_results)
            logger.info(
                f"Found {total_vulnerabilities} vulnerabilities: {severity_counts}"
            )
            logger.info(f"Returning {len(scan_results)} vulnerabilities (paginated)")

            # Add limitation message if profiles were requested but Maven unavailable
            scan_limitations = None
            if include_profiles and not maven_available:
                scan_limitations = [
                    "Maven not available - scanning workspace without profile resolution",
                    "Profile-specific dependencies may not be accurately reflected",
                    "Install Maven for accurate profile-based scanning",
                ]

            # Create scan result
            scan_result = JavaSecurityScanResult(
                scan_mode=scan_mode_desc,
                vulnerabilities_found=total_vulnerabilities > 0,
                total_vulnerabilities=total_vulnerabilities,
                modules_scanned=["."],
                profiles_activated=include_profiles,
                severity_counts=severity_counts,
                vulnerabilities=scan_results,
                pagination=pagination_info,
                scan_limitations=scan_limitations,
                recommendations=None,
                maven_available=maven_available,
            )

        return format_success_response(tool_name, scan_result.model_dump())

    except Exception as e:
        return _handle_scan_error(e, tool_name)
