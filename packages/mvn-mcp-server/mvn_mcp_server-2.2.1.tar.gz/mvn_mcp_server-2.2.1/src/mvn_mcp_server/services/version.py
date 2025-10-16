"""Version service for mvn MCP Server.

This module provides a unified approach to version parsing, comparison,
and filtering based on semantic versioning principles.
"""

import re
import logging
import functools
from typing import List, Tuple, Optional, Dict

# Set up logging
logger = logging.getLogger("mvn-mcp-server")


class VersionService:
    """Service for handling Maven version parsing, comparison, and filtering.

    This service centralizes all version-related logic, providing a consistent
    approach to working with various version formats.
    """

    @staticmethod
    def _extract_qualifier(version_string: str) -> Tuple[str, str]:
        """Extract qualifier from version string.

        Returns:
            Tuple of (base_version, qualifier)
        """
        qualifier = ""
        base_version = version_string

        # Extract qualifier if present (e.g., "1.2.3-SNAPSHOT" -> "1.2.3", "-SNAPSHOT")
        if "-" in version_string:
            base_version, qualifier = version_string.split("-", 1)
            qualifier = f"-{qualifier}"  # Preserve the hyphen for comparison
        elif "." in version_string and not version_string.replace(".", "").isdigit():
            # Handle format like "1.2.3.Final"
            parts = version_string.split(".")
            for i, part in enumerate(parts):
                if not part.isdigit():
                    base_version = ".".join(parts[:i])
                    qualifier = f".{'.'.join(parts[i:])}"
                    break

        return base_version, qualifier

    @staticmethod
    def _try_semver_patterns(base_version: str) -> Optional[List[int]]:
        """Try to match standard semver patterns.

        Returns:
            List of version components if matched, None otherwise
        """
        # Standard semver pattern (MAJOR.MINOR.PATCH)
        semver_match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", base_version)
        if semver_match:
            major, minor, patch = map(int, semver_match.groups())
            return [major, minor, patch]

        # Partial semver pattern (MAJOR.MINOR)
        partial_match = re.match(r"^(\d+)\.(\d+)$", base_version)
        if partial_match:
            major, minor = map(int, partial_match.groups())
            return [major, minor, 0]

        return None

    @staticmethod
    def _try_calendar_version(base_version: str) -> Optional[List[int]]:
        """Try to parse as calendar version (YYYYMMDD).

        Returns:
            List of date components if valid calendar version, None otherwise
        """
        if len(base_version) != 8:
            return None

        try:
            year_candidate = int(base_version[:4])
            if not (1900 <= year_candidate <= 2100):
                return None

            year = year_candidate
            month = int(base_version[4:6])
            day = int(base_version[6:8])

            # Validate that it looks like a real date
            if 1 <= month <= 12 and 1 <= day <= 31:
                logger.debug(
                    f"Parsed calendar version {base_version} as {year}.{month}.{day}"
                )
                return [year, month, day]
        except (ValueError, IndexError):
            logger.debug(
                f"Failed to parse calendar version from '{base_version}'.",
                exc_info=True,
            )

        return None

    @staticmethod
    def _try_simple_numeric(base_version: str) -> Optional[List[int]]:
        """Try to parse as simple numeric version.

        Returns:
            List with single major component if numeric, None otherwise
        """
        simple_match = re.match(r"^(\d+)$", base_version)
        if simple_match:
            major = int(simple_match.group(1))

            # Check if it might be a calendar version first
            calendar_result = VersionService._try_calendar_version(base_version)
            if calendar_result:
                return calendar_result

            return [major, 0, 0]

        return None

    @staticmethod
    def _extract_numeric_components(base_version: str) -> List[int]:
        """Extract numeric components from dotted version string.

        Returns:
            List of numeric components, padded to at least 3 elements
        """
        components = []
        for part in base_version.split("."):
            if part.isdigit():
                components.append(int(part))
            else:
                break

        if not components:
            logger.warning(
                f"Could not parse any numeric components from version: {base_version}"
            )
            return [0, 0, 0]

        # Pad with zeros to ensure at least [major, minor, patch]
        while len(components) < 3:
            components.append(0)

        return components

    @staticmethod
    def parse_version(version_string: str) -> Tuple[List[int], str]:
        """Parse a version string into numeric components and qualifier.

        Supports multiple version formats:
        - Standard semver (MAJOR.MINOR.PATCH)
        - Calendar format (20231013)
        - Simple numeric (5)
        - Partial semver (1.0)

        Args:
            version_string: Version string to parse

        Returns:
            Tuple of (numeric_components, qualifier)
            where numeric_components is a list of integers
            and qualifier is the non-numeric suffix (if any)
        """
        if not version_string:
            return [], ""

        # Extract qualifier from version string
        base_version, qualifier = VersionService._extract_qualifier(version_string)

        # Try different parsing strategies
        components = VersionService._try_semver_patterns(base_version)
        if components:
            return components, qualifier

        components = VersionService._try_simple_numeric(base_version)
        if components:
            return components, qualifier

        # Fallback: extract any numeric parts
        components = VersionService._extract_numeric_components(base_version)
        if components == [0, 0, 0] and base_version != "0":
            # If we couldn't parse anything and it's not actually "0", return the whole string as qualifier
            return [0, 0, 0], version_string

        return components, qualifier

    @staticmethod
    def _handle_empty_versions(version1: str, version2: str) -> Optional[int]:
        """Handle comparison of empty or None versions.

        Returns:
            Comparison result if one or both versions are empty, None otherwise
        """
        if not version1 and version2:
            return -1
        if version1 and not version2:
            return 1
        if not version1 and not version2:
            return 0
        return None

    @staticmethod
    def _compare_numeric_components(
        v1_numeric: List[int], v2_numeric: List[int]
    ) -> Optional[int]:
        """Compare numeric version components.

        Returns:
            Comparison result if components differ, None if equal
        """
        # Compare numeric parts component by component
        for c1, c2 in zip(v1_numeric, v2_numeric):
            if c1 < c2:
                return -1
            if c1 > c2:
                return 1

        # If one version has more numeric components, it's usually newer
        if len(v1_numeric) < len(v2_numeric):
            return -1
        if len(v1_numeric) > len(v2_numeric):
            return 1

        return None  # Numeric components are equal

    @staticmethod
    def _handle_final_qualifier_special_case(
        v1_qualifier: str, v2_qualifier: str
    ) -> Optional[int]:
        """Handle special case for .Final qualifier.

        Returns:
            Comparison result if .Final special case applies, None otherwise
        """
        if v1_qualifier.lower() == ".final" and not v2_qualifier:
            return 1
        if v2_qualifier.lower() == ".final" and not v1_qualifier:
            return -1
        return None

    @staticmethod
    def _handle_empty_qualifiers(v1_qualifier: str, v2_qualifier: str) -> Optional[int]:
        """Handle comparison when one qualifier is empty.

        Returns:
            Comparison result if one qualifier is empty, None otherwise
        """
        # No qualifier is considered higher than any qualifier (except .Final)
        if not v1_qualifier and v2_qualifier:
            return 1
        if v1_qualifier and not v2_qualifier:
            return -1
        return None

    @staticmethod
    def _get_qualifier_ranks() -> Dict[str, int]:
        """Get qualifier ranking dictionary."""
        return {
            "final": 100,
            "release": 90,
            "ga": 80,
            "": 70,  # No qualifier is high but below explicit final/release
            "rc": 60,
            "cr": 50,
            "beta": 40,
            "alpha": 30,
            "snapshot": 10,
        }

    @staticmethod
    def _get_qualifier_rank(qualifier: str) -> int:
        """Get the rank of a qualifier."""
        qualifier_ranks = VersionService._get_qualifier_ranks()
        q_type = qualifier.lower().replace("-", "").replace(".", "")

        rank = 0
        for q_key, q_rank in qualifier_ranks.items():
            if q_key in q_type:
                rank = max(rank, q_rank)
        return rank

    @staticmethod
    def _compare_qualifiers(v1_qualifier: str, v2_qualifier: str) -> int:
        """Compare version qualifiers."""
        # Handle special cases first
        final_result = VersionService._handle_final_qualifier_special_case(
            v1_qualifier, v2_qualifier
        )
        if final_result is not None:
            return final_result

        empty_result = VersionService._handle_empty_qualifiers(
            v1_qualifier, v2_qualifier
        )
        if empty_result is not None:
            return empty_result

        # Compare by qualifier ranks
        v1_rank = VersionService._get_qualifier_rank(v1_qualifier)
        v2_rank = VersionService._get_qualifier_rank(v2_qualifier)

        if v1_rank != v2_rank:
            return 1 if v1_rank > v2_rank else -1

        # Default lexicographical comparison for qualifiers with same rank
        if v1_qualifier < v2_qualifier:
            return -1
        if v1_qualifier > v2_qualifier:
            return 1

        return 0

    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """Compare two version strings semantically.

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        # Handle empty versions
        empty_result = VersionService._handle_empty_versions(version1, version2)
        if empty_result is not None:
            return empty_result

        # Parse version components
        v1_numeric, v1_qualifier = VersionService.parse_version(version1)
        v2_numeric, v2_qualifier = VersionService.parse_version(version2)

        # Compare numeric components
        numeric_result = VersionService._compare_numeric_components(
            v1_numeric, v2_numeric
        )
        if numeric_result is not None:
            return numeric_result

        # Compare qualifiers
        return VersionService._compare_qualifiers(v1_qualifier, v2_qualifier)

    @staticmethod
    def _validate_target_component(target_component: str) -> None:
        """Validate the target component parameter."""
        if target_component not in ["major", "minor", "patch"]:
            raise ValueError(
                f"Invalid target_component: {target_component}. "
                f"Must be one of 'major', 'minor', or 'patch'"
            )

    @staticmethod
    def _prepare_reference_components(reference_version: str) -> Tuple[int, int, int]:
        """Parse and prepare reference version components."""
        ref_components, _ = VersionService.parse_version(reference_version)

        # Ensure ref_components has at least 3 elements
        while len(ref_components) < 3:
            ref_components.append(0)

        return ref_components[0], ref_components[1], ref_components[2]

    @staticmethod
    def _remove_prerelease_versions(versions: List[str]) -> List[str]:
        """Remove snapshot, alpha, beta, rc versions from the list."""
        filtered_versions = []
        prerelease_qualifiers = ["snapshot", "alpha", "beta", "rc", "-m", ".m"]

        for version in versions:
            lower_version = version.lower()
            # Skip pre-release versions
            if any(qualifier in lower_version for qualifier in prerelease_qualifiers):
                continue
            filtered_versions.append(version)

        return filtered_versions

    @staticmethod
    def _filter_by_component(
        versions: List[str], target_component: str, ref_major: int, ref_minor: int
    ) -> List[str]:
        """Filter versions by the specified component."""
        if target_component == "major":
            # For major, just use all stable versions
            return versions
        elif target_component == "minor":
            # For minor, filter versions matching the major component
            return [
                v
                for v in versions
                if VersionService.parse_version(v)[0][0] == ref_major
            ]
        elif target_component == "patch":
            # For patch, filter versions matching the major.minor components
            return [
                v
                for v in versions
                if (
                    VersionService.parse_version(v)[0][0] == ref_major
                    and VersionService.parse_version(v)[0][1] == ref_minor
                )
            ]

        return []

    @staticmethod
    def _handle_empty_filter_result(
        target_component: str, versions: List[str], reference_version: str
    ) -> List[str]:
        """Handle fallback when no versions match the filter."""
        if target_component == "patch":
            # Fall back to minor if patch filter returned no results
            logger.debug("No versions match patch filter, falling back to minor")
            return VersionService.filter_versions(versions, "minor", reference_version)
        elif target_component == "minor":
            # Fall back to all versions if minor filter returned no results
            logger.debug("No versions match minor filter, falling back to major")
            return VersionService.filter_versions(versions, "major", reference_version)

        return []

    @staticmethod
    def filter_versions(
        versions: List[str], target_component: str, reference_version: str
    ) -> List[str]:
        """Filter versions based on target component (major, minor, patch).

        Args:
            versions: List of version strings to filter
            target_component: Component to filter by ("major", "minor", or "patch")
            reference_version: Reference version to compare against

        Returns:
            Filtered list of version strings

        Raises:
            ValueError: If target_component is invalid
        """
        # Validate input
        VersionService._validate_target_component(target_component)

        # Parse reference version
        ref_major, ref_minor, ref_patch = VersionService._prepare_reference_components(
            reference_version
        )

        # Remove pre-release versions
        stable_versions = VersionService._remove_prerelease_versions(versions)

        # Filter based on target component
        component_filtered = VersionService._filter_by_component(
            stable_versions, target_component, ref_major, ref_minor
        )

        # Handle empty results with fallback
        if not component_filtered:
            return VersionService._handle_empty_filter_result(
                target_component, versions, reference_version
            )

        return component_filtered

    @staticmethod
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

        # Special handling for '.Final' versions which should be prioritized
        final_versions = [v for v in versions if ".Final" in v]
        if final_versions:
            return final_versions[0]

        # Filter out SNAPSHOT versions if needed
        filtered_versions = versions
        if not include_snapshots:
            filtered_versions = [v for v in versions if "snapshot" not in v.lower()]

            # If filtering removed all versions, fall back to original list
            if not filtered_versions and versions:
                filtered_versions = versions

        # Sort versions using semantic versioning comparison
        def version_comparator(v1, v2):
            return VersionService.compare_versions(v1, v2)

        sorted_versions = sorted(
            filtered_versions,
            key=functools.cmp_to_key(version_comparator),
            reverse=True,
        )

        return sorted_versions[0] if sorted_versions else ""

    @staticmethod
    def is_date_based_version(version: str) -> bool:
        """Check if a version appears to be date-based (YYYYMMDD format).

        Args:
            version: Version string to check

        Returns:
            True if version appears to be date-based, False otherwise
        """
        if not version or not version.isdigit() or len(version) != 8:
            return False

        try:
            year = int(version[:4])
            month = int(version[4:6])
            day = int(version[6:8])
            # Check for valid date range
            return 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31
        except (ValueError, IndexError):
            return False
