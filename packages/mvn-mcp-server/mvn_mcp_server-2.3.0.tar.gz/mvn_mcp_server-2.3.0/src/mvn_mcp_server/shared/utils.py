"""Utility functions for mvn MCP Server.

This module contains helper functions for API calls, response formatting, and error handling.
"""

import re
import functools
from typing import Dict, Any, Optional, List

from fastmcp.exceptions import ValidationError

from mvn_mcp_server.shared.data_types import ErrorCode


def format_error_response(
    error_code: ErrorCode, error_message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format a standardized error response.

    Args:
        error_code: The error code enum value
        error_message: Human-readable error message
        details: Optional additional details about the error

    Returns:
        Formatted error response dictionary
    """
    response = {"error": {"code": error_code.value, "message": error_message}}

    if details:
        response["error"]["details"] = details

    return response


def validate_maven_dependency(dependency: str) -> tuple[str, str]:
    """Validate Maven dependency string and extract groupId and artifactId.

    Args:
        dependency: Maven dependency in groupId:artifactId format

    Returns:
        Tuple of (groupId, artifactId)

    Raises:
        ValidationError: If dependency format is invalid
    """
    if not dependency or not isinstance(dependency, str):
        raise ValidationError("Dependency must be a non-empty string")

    parts = dependency.split(":")
    if len(parts) != 2:
        raise ValidationError("Dependency must be in groupId:artifactId format")

    group_id, artifact_id = parts
    if not group_id or not artifact_id:
        raise ValidationError("Both groupId and artifactId must be non-empty")

    return group_id, artifact_id


def validate_version_string(version: str) -> str:
    """Validate Maven version string.

    Args:
        version: Version string to validate

    Returns:
        Validated version string

    Raises:
        ValidationError: If version format is invalid
    """
    if not version or not isinstance(version, str):
        raise ValidationError("Version must be a non-empty string")

    # Basic version validation pattern
    # Allows standard versions like 1.2.3, 1.2.3-SNAPSHOT, 1.2.3.Final, etc.
    version_pattern = r"^[\d]+(\.[\d]+)*([-.][\w]+)*$"
    if not re.match(version_pattern, version):
        raise ValidationError(f"Invalid version format: {version}")

    return version


def determine_packaging(packaging: str, artifact_id: str) -> str:
    """Determine correct packaging based on artifact ID or specified packaging.

    Args:
        packaging: User-specified packaging (jar, war, etc.)
        artifact_id: The artifact ID from the dependency

    Returns:
        The determined packaging type
    """
    # If artifact ends with -bom or -dependencies, it's likely a POM
    if artifact_id.endswith(("-bom", "-dependencies")):
        return "pom"

    # Otherwise use the provided packaging or default to jar
    return packaging.lower() if packaging else "jar"


def parse_version_components(version: str) -> tuple[List[int], str]:
    """Parse a version string into numeric components and qualifier.

    Args:
        version: Version string (e.g., "1.2.3-SNAPSHOT")

    Returns:
        Tuple of (numeric_components, qualifier)
        where numeric_components is a list of integers
        and qualifier is the non-numeric suffix (if any)
    """
    # Split version into numeric part and qualifier
    match = re.match(r"^([\d]+(?:\.[\d]+)*)([-.].*)?$", version)
    if not match:
        return [], version

    numeric_part, qualifier = match.groups()
    if qualifier is None:
        qualifier = ""

    # Convert numeric components to integers
    components = [int(part) for part in numeric_part.split(".")]

    return components, qualifier


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings semantically.

    This function delegates to the VersionService for consistent comparison logic.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    # Import here to avoid circular imports
    from mvn_mcp_server.services.version import VersionService

    return VersionService.compare_versions(version1, version2)


def get_latest_version(versions: List[str], include_snapshots: bool = False) -> str:
    """Find the latest version from a list of versions.

    Args:
        versions: List of version strings
        include_snapshots: Whether to include SNAPSHOT versions

    Returns:
        The latest version string

    Raises:
        ValueError: If no valid versions are found
    """
    if not versions:
        raise ValueError("No versions provided")

    # Filter out SNAPSHOT versions if needed
    filtered_versions = versions
    if not include_snapshots:
        filtered_versions = [v for v in versions if "snapshot" not in v.lower()]

        # If filtering removed all versions, fall back to original list
        if not filtered_versions and versions:
            filtered_versions = versions

    # Sort versions using semantic versioning comparison
    def version_comparator(v1, v2):
        return compare_versions(v1, v2)

    sorted_versions = sorted(
        filtered_versions, key=functools.cmp_to_key(version_comparator), reverse=True
    )

    return sorted_versions[0] if sorted_versions else ""
