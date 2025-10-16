"""Enhanced Maven version checking tool.

This module implements a comprehensive tool to check Maven version existence
and retrieve all version updates in a single call.
"""

import logging
from typing import Dict, Any, Optional, Tuple

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


def check_version(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Check a Maven dependency version and provide all version update information.

    Args:
        dependency: Maven dependency in groupId:artifactId format
        version: Version string to check and use as reference
        packaging: Package type (jar, war, etc.), defaults to "jar"
        classifier: Optional classifier

    Returns:
        Dictionary with comprehensive version information:
        - exists: Boolean indicating if the version exists
        - current_version: The provided version
        - latest_versions: Dict of latest versions for each component (major, minor, patch)
        - update_available: Dict of booleans indicating if updates are available

    Raises:
        ValidationError: If input parameters are invalid
        ResourceError: If there's an issue connecting to Maven Central
        ToolError: For other unexpected errors
    """
    tool_name = "check_version"

    try:
        # Validate inputs
        group_id, artifact_id = validate_maven_dependency(dependency)
        validated_version = validate_version_string(version)

        # Determine correct packaging (automatically use "pom" for BOM dependencies)
        actual_packaging = determine_packaging(packaging, artifact_id)

        # Log the input parameters
        logger.debug(
            f"Enhanced version check for: {group_id}:{artifact_id}:{validated_version} "
            f"(packaging: {actual_packaging}, classifier: {classifier})"
        )

        # Check if the specific version exists
        exists = maven_api.check_artifact_exists(
            group_id, artifact_id, validated_version, actual_packaging, classifier
        )

        # Get all available versions
        all_versions = maven_api.get_all_versions(group_id, artifact_id)

        # Find latest versions for each component
        latest_versions, update_available = _get_latest_component_versions(
            all_versions,
            validated_version,
            group_id,
            artifact_id,
            actual_packaging,
            classifier,
        )

        # Prepare the result data
        result = {
            "exists": exists,
            "current_version": validated_version,
            "latest_versions": latest_versions,
            "update_available": update_available,
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
        logger.error(f"Unexpected error in enhanced version check: {str(e)}")
        raise ToolError(
            f"Unexpected error in enhanced version check: {str(e)}",
            {"error_code": ErrorCode.INTERNAL_SERVER_ERROR},
        )


def _get_latest_component_versions(
    versions: list[str],
    reference_version: str,
    group_id: str,
    artifact_id: str,
    packaging: str,
    classifier: Optional[str] = None,
) -> Tuple[Dict[str, str], Dict[str, bool]]:
    """Get the latest version for each semantic version component.

    Args:
        versions: List of all available versions
        reference_version: Reference version for comparison
        group_id: Maven group ID
        artifact_id: Maven artifact ID
        packaging: Package type
        classifier: Optional classifier

    Returns:
        Tuple of (latest_versions, update_available) dictionaries
    """
    components = ["major", "minor", "patch"]
    latest_versions = {}
    update_available = {}

    # Find latest version for each component
    for component in components:
        filtered_versions = version_service.filter_versions(
            versions, component, reference_version
        )

        # If we have filtered versions, get the latest
        if filtered_versions:
            latest_version = version_service.get_latest_version(filtered_versions)

            # Verify the version exists with the current packaging/classifier
            if classifier:
                exists = maven_api.check_artifact_exists(
                    group_id, artifact_id, latest_version, packaging, classifier
                )

                # If it doesn't exist with the classifier, try to find one that does
                if not exists:
                    for ver in filtered_versions:
                        if ver != latest_version:
                            exists = maven_api.check_artifact_exists(
                                group_id, artifact_id, ver, packaging, classifier
                            )
                            if exists:
                                latest_version = ver
                                break

            latest_versions[component] = latest_version

            # Determine if an update is available by comparing with reference version
            # A version is considered an update if it's different and higher than the reference
            update_available[component] = (
                latest_version != reference_version
                and version_service.compare_versions(latest_version, reference_version)
                > 0
            )
        else:
            # Use reference version as fallback if no filtered versions
            latest_versions[component] = reference_version
            update_available[component] = False

    return latest_versions, update_available
