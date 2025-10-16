"""Tests for the Maven version checking tools.

This module tests the enhanced check_version tool which provides
comprehensive version information.
"""

import pytest
from unittest.mock import patch

from fastmcp.exceptions import ValidationError, ResourceError, ToolError

from mvn_mcp_server.tools.check_version import (
    check_version,
    _get_latest_component_versions,
)
from mvn_mcp_server.services.maven_api import MavenApiService
from mvn_mcp_server.services.version import VersionService
from mvn_mcp_server.services.response import format_success_response


class TestEnhancedVersionCheck:
    """Tests for the enhanced check_version function."""

    @patch("mvn_mcp_server.tools.check_version._get_latest_component_versions")
    @patch.object(MavenApiService, "get_all_versions")
    @patch.object(MavenApiService, "check_artifact_exists")
    def test_successful_check(
        self, mock_check_exists, mock_get_all_versions, mock_get_component_versions
    ):
        """Test a successful enhanced version check."""
        # Set up mocks
        mock_check_exists.return_value = True
        mock_get_all_versions.return_value = ["5.2.10", "5.3.10", "5.3.11", "6.0.0"]

        latest_versions = {"major": "6.0.0", "minor": "5.3.11", "patch": "5.3.11"}
        update_available = {"major": True, "minor": True, "patch": True}
        mock_get_component_versions.return_value = (latest_versions, update_available)

        # Execute the function
        result = check_version("org.springframework:spring-core", "5.3.10")

        # Check the result
        expected_result = format_success_response(
            "check_version",
            {
                "exists": True,
                "current_version": "5.3.10",
                "latest_versions": latest_versions,
                "update_available": update_available,
            },
        )
        assert result == expected_result

        # Verify mock calls
        mock_check_exists.assert_called_once_with(
            "org.springframework", "spring-core", "5.3.10", "jar", None
        )
        mock_get_all_versions.assert_called_once_with(
            "org.springframework", "spring-core"
        )
        mock_get_component_versions.assert_called_once()

    @patch("mvn_mcp_server.tools.check_version._get_latest_component_versions")
    @patch.object(MavenApiService, "get_all_versions")
    @patch.object(MavenApiService, "check_artifact_exists")
    def test_nonexistent_version(
        self, mock_check_exists, mock_get_all_versions, mock_get_component_versions
    ):
        """Test with a version that doesn't exist."""
        # Set up mocks
        mock_check_exists.return_value = False
        mock_get_all_versions.return_value = ["5.2.10", "5.3.11", "6.0.0"]

        latest_versions = {"major": "6.0.0", "minor": "5.3.11", "patch": "5.3.11"}
        update_available = {"major": True, "minor": True, "patch": True}
        mock_get_component_versions.return_value = (latest_versions, update_available)

        # Execute the function
        result = check_version(
            "org.springframework:spring-core", "5.3.10"  # This version doesn't exist
        )

        # Check the result
        expected_result = format_success_response(
            "check_version",
            {
                "exists": False,
                "current_version": "5.3.10",
                "latest_versions": latest_versions,
                "update_available": update_available,
            },
        )
        assert result == expected_result

    def test_invalid_dependency_format(self):
        """Test with an invalid dependency format."""
        with pytest.raises(ValidationError):
            check_version("org.springframework.spring-core", "5.3.10")  # Invalid format

    def test_invalid_version_format(self):
        """Test with an invalid version format."""
        with pytest.raises(ValidationError):
            check_version(
                "org.springframework:spring-core", ""  # Invalid empty version
            )

    @patch.object(MavenApiService, "check_artifact_exists")
    def test_resource_error(self, mock_check_exists):
        """Test handling of ResourceError."""
        mock_check_exists.side_effect = ResourceError("API error")

        with pytest.raises(ResourceError):
            check_version("org.springframework:spring-core", "5.3.10")

    @patch.object(MavenApiService, "check_artifact_exists")
    def test_unexpected_exception(self, mock_check_exists):
        """Test handling of unexpected exceptions."""
        mock_check_exists.side_effect = Exception("Unexpected error")

        with pytest.raises(ToolError):
            check_version("org.springframework:spring-core", "5.3.10")


class TestGetLatestComponentVersions:
    """Tests for the _get_latest_component_versions helper function."""

    @patch.object(VersionService, "compare_versions")
    @patch.object(VersionService, "get_latest_version")
    @patch.object(VersionService, "filter_versions")
    def test_successful_component_versions(
        self, mock_filter, mock_get_latest, mock_compare
    ):
        """Test getting latest component versions successfully."""

        # Set up mocks
        def mock_filter_side_effect(versions, component, ref_version):
            if component == "major":
                return ["5.0.0", "6.0.0", "7.0.0"]
            elif component == "minor":
                return ["5.1.0", "5.2.0", "5.3.0"]
            else:  # patch
                return ["5.3.9", "5.3.10", "5.3.11"]

        mock_filter.side_effect = mock_filter_side_effect

        def mock_get_latest_side_effect(versions):
            if "7.0.0" in versions:
                return "7.0.0"
            elif "5.3.0" in versions:
                return "5.3.0"
            else:
                return "5.3.11"

        mock_get_latest.side_effect = mock_get_latest_side_effect

        # For checking if updates are available (all are greater than reference)
        mock_compare.return_value = 1

        # Execute the function
        versions = [
            "5.0.0",
            "5.1.0",
            "5.2.0",
            "5.3.0",
            "5.3.9",
            "5.3.10",
            "5.3.11",
            "6.0.0",
            "7.0.0",
        ]
        latest_versions, update_available = _get_latest_component_versions(
            versions,
            "5.3.0",  # Reference version
            "org.springframework",
            "spring-core",
            "jar",
        )

        # Check the result
        expected_latest_versions = {
            "major": "7.0.0",
            "minor": "5.3.0",
            "patch": "5.3.11",
        }
        expected_update_available = {
            "major": True,
            "minor": False,  # Same as reference
            "patch": True,
        }

        assert latest_versions == expected_latest_versions
        assert update_available["major"] == expected_update_available["major"]
        assert update_available["minor"] == expected_update_available["minor"]
        assert update_available["patch"] == expected_update_available["patch"]

    @patch.object(VersionService, "compare_versions")
    @patch.object(VersionService, "get_latest_version")
    @patch.object(VersionService, "filter_versions")
    def test_no_filtered_versions(self, mock_filter, mock_get_latest, mock_compare):
        """Test behavior when filtering returns no versions."""
        # Set up mocks - filter returns empty lists
        mock_filter.return_value = []

        # Execute the function
        versions = ["5.0.0", "6.0.0"]
        latest_versions, update_available = _get_latest_component_versions(
            versions,
            "5.3.0",  # Reference version
            "org.springframework",
            "spring-core",
            "jar",
        )

        # Check that we fall back to reference version
        expected_latest_versions = {
            "major": "5.3.0",
            "minor": "5.3.0",
            "patch": "5.3.0",
        }
        expected_update_available = {"major": False, "minor": False, "patch": False}

        assert latest_versions == expected_latest_versions
        assert update_available == expected_update_available
