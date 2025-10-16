"""Maven version checking batch tool.

This module implements a batch processing tool to check multiple Maven
dependency versions in a single request.
"""

import logging
import concurrent.futures
from typing import Dict, Any, List

from fastmcp.exceptions import ValidationError, ToolError, ResourceError

from mvn_mcp_server.shared.data_types import (
    ErrorCode,
)
from mvn_mcp_server.services.response import format_success_response
from mvn_mcp_server.services.maven_api import MavenApiService
from mvn_mcp_server.services.version import VersionService
from mvn_mcp_server.tools.check_version import check_version

# Set up logging
logger = logging.getLogger("mvn-mcp-server")

# Create shared instances of services
maven_api = MavenApiService()
version_service = VersionService()


def check_version_batch(dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process multiple Maven dependency version checks in a single batch request.

    Args:
        dependencies: List of dependency objects, each containing:
            - dependency: Maven dependency in groupId:artifactId format
            - version: Version string to check
            - packaging: (Optional) Package type, defaults to "jar"
            - classifier: (Optional) Classifier

    Returns:
        Dictionary with comprehensive batch results:
        - summary: Summary statistics of the batch operation
        - dependencies: List of individual dependency check results

    Raises:
        ValidationError: If input parameters are invalid
        ResourceError: If there's an issue connecting to Maven Central
        ToolError: For other unexpected errors
    """
    try:
        # Validate input format
        if not dependencies or not isinstance(dependencies, list):
            raise ValidationError(
                "Dependencies must be provided as a non-empty list",
                {"error_code": ErrorCode.INVALID_INPUT_FORMAT},
            )

        # Log the batch request
        logger.debug(
            f"Processing batch version check request with {len(dependencies)} dependencies"
        )

        # Process each dependency in parallel
        dependency_results = _process_dependencies_parallel(dependencies)

        # Calculate summary statistics
        summary = _calculate_batch_summary(dependency_results)

        # Prepare the result
        result = {"summary": summary, "dependencies": dependency_results}

        # Return success response
        return format_success_response("check_version_batch", result)

    except ValidationError as e:
        # Re-raise validation errors
        logger.error(f"Validation error in batch request: {str(e)}")
        raise ValidationError(str(e))
    except ResourceError as e:
        # Handle resource errors
        logger.error(f"Resource error in batch request: {str(e)}")
        raise e
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in batch version check: {str(e)}")
        raise ToolError(
            f"Unexpected error in batch version check: {str(e)}",
            {"error_code": ErrorCode.INTERNAL_SERVER_ERROR},
        )


def _process_dependencies_parallel(
    dependencies: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Process dependencies in parallel to improve performance.

    Args:
        dependencies: List of dependency objects

    Returns:
        List of processed dependency results
    """
    # Deduplicate dependencies to avoid redundant checks
    unique_deps = _deduplicate_dependencies(dependencies)

    # Create a map from unique key to original index positions
    dep_map = {}
    for i, dep in enumerate(dependencies):
        key = _dependency_key(dep)
        if key not in dep_map:
            dep_map[key] = []
        dep_map[key].append(i)

    # Results list with placeholders for each input dependency
    results = [None] * len(dependencies)

    # Process unique dependencies in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all unique dependencies for processing
        future_to_dep = {
            executor.submit(_process_single_dependency, dep): _dependency_key(dep)
            for dep in unique_deps
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_dep):
            key = future_to_dep[future]
            try:
                result = future.result()
                # Map the result to all original positions of this dependency
                for idx in dep_map[key]:
                    results[idx] = result
            except Exception as e:
                logger.error(f"Error processing dependency {key}: {str(e)}")
                error_result = {
                    "dependency": key.split("::")[0],
                    "status": "error",
                    "error": {
                        "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                        "message": str(e),
                    },
                }
                # Map the error to all original positions of this dependency
                for idx in dep_map[key]:
                    results[idx] = error_result

    # Ensure all dependencies have a result
    for i, result in enumerate(results):
        if result is None:
            dep = dependencies[i].get("dependency", "unknown")
            results[i] = {
                "dependency": dep,
                "status": "error",
                "error": {
                    "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                    "message": "Failed to process dependency",
                },
            }

    return results


def _process_single_dependency(dependency_item: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single dependency check.

    Args:
        dependency_item: Dependency object with parameters

    Returns:
        Processed dependency result
    """
    dependency = dependency_item.get("dependency", "")
    version = dependency_item.get("version", "")
    packaging = dependency_item.get("packaging", "jar")
    classifier = dependency_item.get("classifier")

    try:
        # Use the individual check_version function
        result = check_version(dependency, version, packaging, classifier)

        # Extract the data from the response
        if result["status"] == "success":
            return {
                "dependency": dependency,
                "status": "success",
                "result": result["result"],
            }
        else:
            return {
                "dependency": dependency,
                "status": "error",
                "error": result.get(
                    "error",
                    {
                        "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                        "message": "Unknown error",
                    },
                ),
            }
    except Exception as e:
        logger.error(f"Error checking {dependency}:{version}: {str(e)}")
        return {
            "dependency": dependency,
            "status": "error",
            "error": {"code": ErrorCode.INTERNAL_SERVER_ERROR.value, "message": str(e)},
        }


def _deduplicate_dependencies(
    dependencies: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Deduplicate dependencies to avoid redundant API calls.

    Args:
        dependencies: List of dependency objects

    Returns:
        List of unique dependency objects
    """
    seen = set()
    unique_deps = []

    for dep in dependencies:
        key = _dependency_key(dep)
        if key not in seen:
            seen.add(key)
            unique_deps.append(dep)

    return unique_deps


def _dependency_key(dependency_item: Dict[str, Any]) -> str:
    """Create a unique key for a dependency object.

    Args:
        dependency_item: Dependency object

    Returns:
        String key uniquely identifying the dependency
    """
    dependency = dependency_item.get("dependency", "")
    version = dependency_item.get("version", "")
    packaging = dependency_item.get("packaging", "jar")
    classifier = dependency_item.get("classifier", "none")
    return f"{dependency}::{version}::{packaging}::{classifier}"


def _calculate_batch_summary(
    dependency_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate summary statistics for the batch operation.

    Args:
        dependency_results: List of processed dependency results

    Returns:
        Dictionary with summary statistics
    """
    total = len(dependency_results)
    success_count = sum(1 for r in dependency_results if r.get("status") == "success")
    failed_count = total - success_count

    # Count updates available
    updates = {"major": 0, "minor": 0, "patch": 0}

    for result in dependency_results:
        if result.get("status") == "success":
            result_data = result.get("result", {})
            update_info = result_data.get("update_available", {})

            for component in ["major", "minor", "patch"]:
                if update_info.get(component, False):
                    updates[component] += 1

    return {
        "total": total,
        "success": success_count,
        "failed": failed_count,
        "updates_available": updates,
    }
