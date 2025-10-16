"""Java security scanning tool for Maven projects.

This module implements security scanning for Java projects using Trivy.
Supports profile-based scanning by generating and scanning effective POMs for child modules specified in profiles.
"""

import os
import subprocess
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict

import defusedxml.ElementTree as ET

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


def _extract_module_paths_for_profile(
    parent_pom_path: Path, profile_id: str
) -> List[Path]:
    """Extract module paths from a Maven profile in the parent POM.

    Args:
        parent_pom_path: Path to the parent pom.xml
        profile_id: Profile ID to extract modules for

    Returns:
        List of Path objects pointing to child module directories.
        Returns empty list if profile is not found or has no valid module paths.

    Raises:
        ValidationError: If parent POM cannot be parsed
    """
    try:
        tree = ET.parse(parent_pom_path)
        root = tree.getroot()

        # Maven uses a namespace, need to handle it
        namespace = {"mvn": "http://maven.apache.org/POM/4.0.0"}

        # Try without namespace first (some POMs don't use it)
        profiles = root.findall(".//profile")
        if not profiles:
            # Try with namespace
            profiles = root.findall(".//mvn:profile", namespace)

        # Find the matching profile
        for profile in profiles:
            profile_id_elem = profile.find("id") or profile.find("mvn:id", namespace)
            if profile_id_elem is not None and profile_id_elem.text == profile_id:
                # Extract module paths
                modules = profile.findall(".//module")
                if not modules:
                    modules = profile.findall(".//mvn:module", namespace)

                module_paths = []
                parent_dir = parent_pom_path.parent

                for module in modules:
                    if module.text:
                        module_path = parent_dir / module.text

                        # Validate that resolved path stays within parent directory
                        try:
                            resolved_module = module_path.resolve()
                            resolved_parent = parent_dir.resolve()

                            # Check path traversal - ensure module is within parent
                            if not str(resolved_module).startswith(
                                str(resolved_parent) + os.sep
                            ):
                                # Also check if it's exactly the parent (edge case)
                                if resolved_module != resolved_parent:
                                    logger.warning(
                                        f"Module path escapes parent directory: {module_path} -> {resolved_module}"
                                    )
                                    continue

                            if resolved_module.exists() and resolved_module.is_dir():
                                module_paths.append(resolved_module)
                            else:
                                logger.warning(
                                    f"Module directory not found: {module_path}"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Error resolving module path '{module_path}': {e}"
                            )
                            continue

                if module_paths:
                    logger.info(
                        f"Found {len(module_paths)} modules for profile '{profile_id}': "
                        f"{[str(p.relative_to(parent_dir)) for p in module_paths]}"
                    )
                    return module_paths
                else:
                    logger.warning(
                        f"Profile '{profile_id}' found but no valid module paths"
                    )
                    return []

        # Profile not found
        logger.warning(f"Profile '{profile_id}' not found in {parent_pom_path}")
        return []

    except ET.ParseError as e:
        raise ValidationError(f"Failed to parse parent POM {parent_pom_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting modules for profile '{profile_id}': {str(e)}")
        raise ValidationError(
            f"Failed to extract modules for profile '{profile_id}': {str(e)}"
        )


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


def _extract_module_name_from_pom_path(pom_file: str) -> str:
    """Extract module name from POM file path.

    Args:
        pom_file: Path to POM file (e.g., "partition-core-plus/pom.xml")

    Returns:
        Module name extracted from path

    Examples:
        "partition-core-plus/pom.xml" -> "partition-core-plus"
        "provider/partition-azure/pom.xml" -> "provider/partition-azure"
        "pom.xml" -> "."
    """
    path = Path(pom_file)

    # If the file is named pom.xml, return the parent directory
    if path.name == "pom.xml":
        parent = path.parent
        # If parent is current directory, return "."
        return "." if str(parent) in ("", ".") else str(parent)

    # If not a pom.xml file, return the path as-is
    return pom_file


def _build_module_summary(
    vulnerabilities: List[JavaVulnerability],
) -> Dict[str, Any]:
    """Build per-module vulnerability summary.

    Groups vulnerabilities by source_location (POM file) and calculates
    severity breakdown for each module.

    Args:
        vulnerabilities: All vulnerabilities found in the scan

    Returns:
        Dict mapping module name to its summary (as dict for JSON serialization)
    """
    from mvn_mcp_server.shared.data_types import ModuleSummary, ModuleSeverityBreakdown

    module_vulns = defaultdict(list)

    # Group vulnerabilities by source_location
    for vuln in vulnerabilities:
        source = vuln.source_location
        module_vulns[source].append(vuln)

    # Build summary for each module
    summary = {}
    for pom_file, vulns in module_vulns.items():
        severity_counts = _calculate_severity_counts(vulns)

        # Extract module name from POM path
        module_name = _extract_module_name_from_pom_path(pom_file)

        module_summary = ModuleSummary(
            pom_file=pom_file,
            vulnerability_count=len(vulns),
            severity_breakdown=ModuleSeverityBreakdown(**severity_counts),
        )

        summary[module_name] = module_summary.model_dump()

    return summary


def _build_affected_modules(
    vulnerabilities: List[JavaVulnerability], severity_filter: List[str]
) -> List[Dict[str, Any]]:
    """Build list of modules affected by filtered severities.

    Only includes modules that have vulnerabilities matching the severity filter.
    Sorted by severity (critical first, then high, etc.) and count.

    Args:
        vulnerabilities: All vulnerabilities found
        severity_filter: Severity levels to include (e.g., ["critical", "high"])

    Returns:
        List of affected modules as dicts (sorted by severity and count)
    """
    from mvn_mcp_server.shared.data_types import AffectedModule

    module_vulns = defaultdict(list)

    # Group by source_location and filter by severity
    filter_lower = [s.lower() for s in severity_filter]
    for vuln in vulnerabilities:
        if vuln.severity.lower() in filter_lower:
            source = vuln.source_location
            module_vulns[source].append(vuln)

    # Build affected modules list
    affected = []
    for pom_file, vulns in module_vulns.items():
        # Calculate severity counts (only filtered severities)
        severity_counts = {}
        for severity in filter_lower:
            count = sum(1 for v in vulns if v.severity.lower() == severity)
            if count > 0:
                severity_counts[severity] = count

        # Extract unique CVE IDs
        cve_ids = sorted(set(v.cve_id for v in vulns if v.cve_id))

        # Extract module name
        module_name = _extract_module_name_from_pom_path(pom_file)

        affected_module = AffectedModule(
            module=module_name,
            pom_file=pom_file,
            severity_counts=severity_counts,
            cve_ids=cve_ids,
            vulnerability_count=len(vulns),
        )

        affected.append(affected_module.model_dump())

    # Sort by severity priority (critical > high > medium > low)
    severity_priority = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}

    def sort_key(module):
        # Get highest severity present
        severities_in_module = module["severity_counts"].keys()
        if not severities_in_module:
            return (999, 0)
        min_priority = min(
            severity_priority.get(sev, 999) for sev in severities_in_module
        )
        # Then by total count (descending)
        return (min_priority, -module["vulnerability_count"])

    affected.sort(key=sort_key)

    return affected


def _compile_module_outputs(
    all_results: List[JavaVulnerability], severity_filter: List[str]
) -> tuple[Dict[str, Any], List[Any]]:
    """Compile module summary and affected modules from scan results.

    This is a shared helper to reduce duplication between different scan paths.

    Args:
        all_results: All vulnerabilities found in the scan
        severity_filter: Severity levels to include in affected modules

    Returns:
        Tuple of (module_summary dict, affected_modules list of AffectedModule objects)
    """
    from mvn_mcp_server.shared.data_types import AffectedModule

    # Build module summary
    module_summary = _build_module_summary(all_results)

    # Build affected modules
    affected_modules_dicts = _build_affected_modules(all_results, severity_filter)

    # Convert dicts to AffectedModule objects for type safety
    affected_modules = [AffectedModule(**m) for m in affected_modules_dicts]

    return module_summary, affected_modules


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
    profile_results: Dict[str, Dict[str, Any]],
    max_results: int,
    offset: int,
    severity_filter: Optional[List[str]] = None,
    maven_available: bool = True,
) -> Dict[str, Any]:
    """Aggregate results from multiple profile scans.

    Args:
        profile_results: Dict mapping profile_id to scan results
        max_results: Maximum results to return
        offset: Pagination offset
        severity_filter: Severity levels included in the scan (default: all levels)
        maven_available: Whether Maven was available for profile scanning

    Returns:
        Aggregated scan results with per-profile breakdown
    """
    if severity_filter is None:
        severity_filter = ["critical", "high", "medium", "low", "unknown"]
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

    # Build module summary and affected modules
    module_summary = _build_module_summary(all_vulnerabilities)
    affected_modules = _build_affected_modules(all_vulnerabilities, severity_filter)

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
        "maven_available": maven_available,
        "module_summary": module_summary,
        "affected_modules": affected_modules,
        "severity_filter_applied": severity_filter,
    }


def _scan_with_profiles(
    workspace_path: Path,
    profiles: List[str],
    severity_filter: List[str],
    max_results: int,
    offset: int,
) -> Dict[str, Any]:
    """Execute profile-based scanning using Maven effective POMs.

    Generates effective POMs for each profile and scans them with Trivy,
    which preserves profile-specific dependency version information.

    Args:
        workspace_path: Path to the Maven project
        profiles: List of profile IDs to scan
        severity_filter: Severity levels to include
        max_results: Maximum results to return
        offset: Pagination offset

    Returns:
        Aggregated profile scan results

    Raises:
        ResourceError: If Trivy operations fail or Maven is not available
        ValidationError: If parent POM cannot be parsed
    """
    logger.info(f"Starting profile-based scanning for profiles: {profiles}")

    parent_pom = workspace_path / "pom.xml"
    if not parent_pom.exists():
        raise ValidationError(f"Parent pom.xml not found at {parent_pom}")

    # Check Maven availability
    maven_available = MavenEffectivePomService.check_maven_availability()
    if not maven_available:
        logger.warning(
            "Maven not available for profile-based scanning. Cannot generate effective POMs."
        )
        raise ResourceError(
            "Maven is not available. Cannot generate effective POMs for profile-based scanning."
        )

    # Generate effective POMs for each profile
    try:
        effective_poms = MavenEffectivePomService.generate_effective_poms_for_profiles(
            workspace_path, profiles
        )
    except Exception as e:
        logger.error(f"Failed to generate effective POMs: {str(e)}")
        raise ResourceError(f"Failed to generate effective POMs: {str(e)}")

    # Scan each profile's effective POM
    profile_results = {}

    try:
        for profile_id in profiles:
            logger.info(f"Processing profile: {profile_id}")

            if profile_id not in effective_poms:
                logger.warning(f"No effective POM generated for profile '{profile_id}'")
                profile_results[profile_id] = {
                    "vulnerabilities": [],
                    "total_vulnerabilities": 0,
                    "severity_counts": _calculate_severity_counts([]),
                }
                continue

            effective_pom_path = effective_poms[profile_id]
            logger.info(
                f"Scanning effective POM for profile '{profile_id}': {effective_pom_path}"
            )

            try:
                # Run Trivy scan on effective POM
                trivy_data = _run_trivy_scan(effective_pom_path)

                # Process results
                vulnerabilities = _process_trivy_results(trivy_data, severity_filter)

                # Tag vulnerabilities with profile
                for vuln in vulnerabilities:
                    vuln.in_profile = profile_id

                logger.info(
                    f"Profile {profile_id}: found {len(vulnerabilities)} vulnerabilities"
                )

                # Calculate severity counts for this profile
                severity_counts = _calculate_severity_counts(vulnerabilities)

                # Store profile results
                profile_results[profile_id] = {
                    "vulnerabilities": vulnerabilities,
                    "total_vulnerabilities": len(vulnerabilities),
                    "severity_counts": severity_counts,
                }

            except Exception as e:
                logger.error(f"Error scanning profile {profile_id}: {str(e)}")
                # Continue with other profiles even if one fails
                profile_results[profile_id] = {
                    "vulnerabilities": [],
                    "total_vulnerabilities": 0,
                    "severity_counts": _calculate_severity_counts([]),
                }
                continue

    finally:
        # Clean up effective POMs
        try:
            MavenEffectivePomService.cleanup_effective_poms()
            logger.info("Cleaned up effective POM files")
        except Exception as e:
            logger.warning(f"Error cleaning up effective POMs: {str(e)}")

    # Aggregate results from all profiles
    aggregated_results = _aggregate_profile_results(
        profile_results, max_results, offset, severity_filter, maven_available
    )

    return aggregated_results


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
        use_profile_scanning = bool(include_profiles)

        if use_profile_scanning:
            # Use profile-based scanning via effective POMs
            logger.info(
                f"Using profile-based scanning for profiles: {include_profiles}"
            )
            try:
                result_data = _scan_with_profiles(
                    workspace_path,
                    include_profiles,
                    severity_filter,
                    max_results,
                    offset,
                )

                # Create scan result from aggregated data
                scan_result = JavaSecurityScanResult(**result_data)
            except ResourceError as e:
                # If Maven is not available, fall back to workspace scanning
                # But only for Maven unavailability, not other Maven errors
                if "not available" in str(e).lower() and "maven" in str(e).lower():
                    logger.info(
                        "Maven not available for profile scanning. Falling back to workspace scan."
                    )
                    maven_available = False

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

                    # Build module summary and affected modules
                    module_summary, affected_modules = _compile_module_outputs(
                        all_results, severity_filter
                    )

                    # Create scan result with limitation note
                    scan_result = JavaSecurityScanResult(
                        scan_mode=scan_mode_desc,
                        vulnerabilities_found=total_vulnerabilities > 0,
                        total_vulnerabilities=total_vulnerabilities,
                        modules_scanned=["."],
                        profiles_activated=include_profiles,
                        severity_counts=severity_counts,
                        vulnerabilities=scan_results,
                        pagination=pagination_info,
                        scan_limitations=[
                            "Maven not available for profile-based scanning - performed workspace scan instead"
                        ],
                        recommendations=None,
                        maven_available=maven_available,
                        module_summary=module_summary,
                        affected_modules=affected_modules,
                        severity_filter_applied=severity_filter,
                    )
                else:
                    raise

        else:
            # Use standard workspace scanning
            maven_available = MavenEffectivePomService.check_maven_availability()

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

            # Build module summary and affected modules
            module_summary, affected_modules = _compile_module_outputs(
                all_results, severity_filter
            )

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
                scan_limitations=None,  # No limitations for standard workspace scan
                recommendations=None,
                maven_available=maven_available,
                module_summary=module_summary,
                affected_modules=affected_modules,
                severity_filter_applied=severity_filter,
            )

        return format_success_response(tool_name, scan_result.model_dump())

    except Exception as e:
        return _handle_scan_error(e, tool_name)
