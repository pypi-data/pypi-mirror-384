"""Maven list available versions tool.

This module implements a tool to provide structured information about all available
versions of a Maven dependency, grouped by minor version tracks.
"""

import logging
from typing import Dict, Any, Optional, List

from fastmcp.exceptions import ValidationError, ToolError, ResourceError

from mvn_mcp_server.shared.data_types import ErrorCode
from mvn_mcp_server.shared.utils import (
    validate_maven_dependency,
    validate_version_string,
    determine_packaging,
)
from mvn_mcp_server.services.maven_api import MavenApiService
from mvn_mcp_server.services.version import VersionService
from mvn_mcp_server.services.response import format_success_response

# Set up logging
logger = logging.getLogger("mvn-mcp-server")

# Create shared instances of services
maven_api = MavenApiService()
version_service = VersionService()


def list_available_versions(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: Optional[str] = None,
    include_all_versions: bool = False,
) -> Dict[str, Any]:
    """List all available versions of a Maven dependency grouped by minor tracks.

    Args:
        dependency: Maven dependency in groupId:artifactId format
        version: Current version string to use as reference
        packaging: Package type (jar, war, etc.), defaults to "jar"
        classifier: Optional classifier
        include_all_versions: Whether to include all versions in the response

    Returns:
        Dictionary with structured version information:
        - current_version: The provided reference version
        - current_exists: Boolean indicating if the current version exists
        - latest_version: The latest overall version
        - minor_tracks: Dict of minor version tracks with latest version and full version list

    Raises:
        ValidationError: If input parameters are invalid
        ResourceError: If there's an issue connecting to Maven Central
        ToolError: For other unexpected errors
    """
    tool_name = "list_available_versions"

    try:
        # Validate inputs
        group_id, artifact_id = validate_maven_dependency(dependency)
        validated_version = validate_version_string(version)

        # Determine correct packaging (automatically use "pom" for BOM dependencies)
        actual_packaging = determine_packaging(packaging, artifact_id)

        # Log the input parameters
        logger.debug(
            f"Listing available versions for: {group_id}:{artifact_id} using reference version {validated_version} "
            f"(packaging: {actual_packaging}, classifier: {classifier}, include_all: {include_all_versions})"
        )

        # Check if the specific version exists
        current_exists = maven_api.check_artifact_exists(
            group_id, artifact_id, validated_version, actual_packaging, classifier
        )

        # Get all available versions
        all_versions = maven_api.get_all_versions(group_id, artifact_id)

        # Remove snapshot and pre-release versions (alpha, beta, RC) which are not suitable for production
        stable_versions = _filter_stable_versions(all_versions)

        # Group versions by major.minor tracks
        minor_tracks = _group_versions_by_minor_track(
            stable_versions, validated_version, include_all_versions
        )

        # Determine the latest overall version
        latest_version = (
            version_service.get_latest_version(stable_versions)
            if stable_versions
            else validated_version
        )

        # Prepare the result data
        result = {
            "current_version": validated_version,
            "current_exists": current_exists,
            "latest_version": latest_version,
            "minor_tracks": minor_tracks,
        }

        # Return success response
        return format_success_response(tool_name, result)

    except ValidationError as e:
        # Re-raise validation errors
        logger.error(f"Validation error: {str(e)}")
        raise ValidationError(str(e))
    except ResourceError as e:
        # Handle resource errors
        logger.error(f"Resource error: {str(e)}")
        raise e
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error listing available versions: {str(e)}")
        raise ToolError(
            f"Unexpected error listing available versions: {str(e)}",
            {"error_code": ErrorCode.INTERNAL_SERVER_ERROR},
        )


def _filter_stable_versions(versions: List[str]) -> List[str]:
    """Filter out snapshot and pre-release versions.

    Args:
        versions: List of all available versions

    Returns:
        List of stable versions
    """
    filtered_versions = []

    for version in versions:
        lower_version = version.lower()
        # Skip pre-release versions
        if any(
            qualifier in lower_version
            for qualifier in [
                "snapshot",
                "alpha",
                "beta",
                "rc",
                "-m",
                ".m",
                "milestone",
                "preview",
                "incubating",
                "ea",
            ]
        ):
            continue
        filtered_versions.append(version)

    return filtered_versions


def _group_versions_by_minor_track(
    versions: List[str], reference_version: str, include_all_versions: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Group versions by major.minor tracks.

    Args:
        versions: List of stable versions
        reference_version: Current version for comparison
        include_all_versions: Whether to include all versions or just the latest per track

    Returns:
        Dictionary mapping major.minor track to version information
    """
    if not versions:
        return {}

    # Parse the reference version to determine its major.minor track
    ref_components, _ = version_service.parse_version(reference_version)
    ref_major, ref_minor = (
        ref_components[:2] if len(ref_components) >= 2 else (ref_components[0], 0)
    )
    ref_track = f"{ref_major}.{ref_minor}"

    # Group versions by major.minor track
    track_map: Dict[str, List[str]] = {}

    for version in versions:
        components, _ = version_service.parse_version(version)

        # Handle versions with insufficient components
        if len(components) < 2:
            components = components + [0] * (2 - len(components))

        major, minor = components[:2]
        track = f"{major}.{minor}"

        if track not in track_map:
            track_map[track] = []

        track_map[track].append(version)

    # Determine the latest version for each track
    result = {}
    for track, track_versions in track_map.items():
        latest_in_track = version_service.get_latest_version(track_versions)

        # Determine if this is the current version's track
        is_current_track = track == ref_track

        # Create the track entry
        track_entry = {"latest": latest_in_track, "is_current_track": is_current_track}

        # Include all versions if requested
        if include_all_versions or is_current_track:
            # Sort versions semantically (newest first)
            sorted_versions = sorted(
                track_versions,
                key=lambda v: version_service.compare_versions(v, "0.0.0"),
                reverse=True,
            )
            track_entry["versions"] = sorted_versions

        result[track] = track_entry

    # Sort tracks by semantic version (newest first)
    sorted_result = {}
    for track in sorted(
        result.keys(), key=lambda t: tuple(map(int, t.split("."))), reverse=True
    ):
        sorted_result[track] = result[track]

    return sorted_result
