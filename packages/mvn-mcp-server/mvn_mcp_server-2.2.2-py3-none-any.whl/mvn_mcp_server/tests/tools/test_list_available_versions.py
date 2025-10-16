"""Tests for the Maven List Available Versions tool.

This module contains tests for the list_available_versions tool that
provides structured information about all available versions of a
Maven dependency, grouped by minor version tracks.
"""

import pytest
from unittest.mock import patch

from fastmcp.exceptions import ValidationError, ResourceError, ToolError

from mvn_mcp_server.tools.list_available_versions import list_available_versions
from mvn_mcp_server.shared.data_types import ErrorCode


class TestListAvailableVersions:
    """Test suite for list_available_versions tool."""

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    @patch("mvn_mcp_server.tools.list_available_versions.version_service")
    def test_successful_list_with_all_versions(
        self, mock_version_service, mock_maven_api
    ):
        """Test successful version listing with all versions included."""
        # Mock dependencies
        mock_maven_api.check_artifact_exists.return_value = True
        mock_maven_api.get_all_versions.return_value = [
            "1.0.0",
            "1.0.1",
            "1.0.2",
            "1.1.0",
            "1.1.1",
            "2.0.0",
            "2.0.1-SNAPSHOT",
            "2.0.2",
        ]

        # Mock version parsing and comparison
        def mock_parse_version(version):
            if version == "1.0.0":
                return [1, 0, 0], ""
            elif version == "1.0.1":
                return [1, 0, 1], ""
            elif version == "1.0.2":
                return [1, 0, 2], ""
            elif version == "1.1.0":
                return [1, 1, 0], ""
            elif version == "1.1.1":
                return [1, 1, 1], ""
            elif version == "2.0.0":
                return [2, 0, 0], ""
            elif version == "2.0.1-SNAPSHOT":
                return [2, 0, 1], "-SNAPSHOT"
            elif version == "2.0.2":
                return [2, 0, 2], ""
            return [0, 0, 0], ""

        mock_version_service.parse_version.side_effect = mock_parse_version

        def mock_compare_versions(v1, v2):
            comp1, _ = mock_parse_version(v1)
            comp2, _ = mock_parse_version(v2)
            if comp1 > comp2:
                return 1
            elif comp1 < comp2:
                return -1
            return 0

        mock_version_service.compare_versions.side_effect = mock_compare_versions
        mock_version_service.get_latest_version.return_value = "2.0.2"

        # Call the function under test
        result = list_available_versions(
            dependency="org.example:library", version="1.0.1", include_all_versions=True
        )

        # Verify success status
        assert result["status"] == "success"
        assert result["tool_name"] == "list_available_versions"

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    @patch("mvn_mcp_server.tools.list_available_versions.version_service")
    def test_successful_list_without_all_versions(
        self, mock_version_service, mock_maven_api
    ):
        """Test successful version listing without all versions (only current track with versions)."""
        # Mock dependencies
        mock_maven_api.check_artifact_exists.return_value = True
        mock_maven_api.get_all_versions.return_value = [
            "1.0.0",
            "1.0.1",
            "1.0.2",
            "1.1.0",
            "1.1.1",
            "2.0.0",
            "2.0.1-SNAPSHOT",
            "2.0.2",
        ]

        # Mock version parsing and comparison
        def mock_parse_version(version):
            if version == "1.0.0":
                return [1, 0, 0], ""
            elif version == "1.0.1":
                return [1, 0, 1], ""
            elif version == "1.0.2":
                return [1, 0, 2], ""
            elif version == "1.1.0":
                return [1, 1, 0], ""
            elif version == "1.1.1":
                return [1, 1, 1], ""
            elif version == "2.0.0":
                return [2, 0, 0], ""
            elif version == "2.0.1-SNAPSHOT":
                return [2, 0, 1], "-SNAPSHOT"
            elif version == "2.0.2":
                return [2, 0, 2], ""
            return [0, 0, 0], ""

        mock_version_service.parse_version.side_effect = mock_parse_version

        def mock_compare_versions(v1, v2):
            comp1, _ = mock_parse_version(v1)
            comp2, _ = mock_parse_version(v2)
            if comp1 > comp2:
                return 1
            elif comp1 < comp2:
                return -1
            return 0

        mock_version_service.compare_versions.side_effect = mock_compare_versions
        mock_version_service.get_latest_version.return_value = "2.0.2"

        # Call the function under test
        result = list_available_versions(
            dependency="org.example:library",
            version="1.0.1",
            include_all_versions=False,
        )

        # Verify success status
        assert result["status"] == "success"
        assert result["tool_name"] == "list_available_versions"

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    @patch("mvn_mcp_server.tools.list_available_versions.version_service")
    def test_empty_versions_list(self, mock_version_service, mock_maven_api):
        """Test behavior when no versions are available."""
        # Mock dependencies
        mock_maven_api.check_artifact_exists.return_value = False
        mock_maven_api.get_all_versions.return_value = []

        mock_version_service.parse_version.return_value = ([1, 0, 0], "")

        # Call the function under test
        result = list_available_versions(
            dependency="org.example:library", version="1.0.0", include_all_versions=True
        )

        # Assertions
        assert result["status"] == "success"

        # Check result data
        data = result["result"]
        assert data["current_version"] == "1.0.0"
        assert data["current_exists"] is False
        assert data["latest_version"] == "1.0.0"  # Falls back to current version
        assert data["minor_tracks"] == {}  # Empty tracks

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    def test_invalid_dependency_format(self, mock_maven_api):
        """Test validation error for invalid dependency format."""
        # Call the function under test with invalid input
        with pytest.raises(ValidationError):
            list_available_versions(dependency="invalid-format", version="1.0.0")

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    def test_empty_version(self, mock_maven_api):
        """Test validation error for empty version."""
        # Call the function under test with empty version
        with pytest.raises(ValidationError):
            list_available_versions(dependency="org.example:library", version="")

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    def test_maven_api_error(self, mock_maven_api):
        """Test handling of Maven API errors."""
        # Mock the API to raise a ResourceError
        mock_maven_api.check_artifact_exists.side_effect = ResourceError(
            "Maven API connection failed", {"error_code": ErrorCode.MAVEN_API_ERROR}
        )

        # Call the function under test
        with pytest.raises(ResourceError) as excinfo:
            list_available_versions(dependency="org.example:library", version="1.0.0")

        # Verify the error message
        assert "Maven API connection failed" in str(excinfo.value)

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    def test_dependency_not_found(self, mock_maven_api):
        """Test handling of dependency not found error."""
        # Mock the API to raise a ResourceError for dependency not found
        mock_maven_api.check_artifact_exists.return_value = False
        mock_maven_api.get_all_versions.side_effect = ResourceError(
            "Dependency org.example:library not found in Maven Central",
            {"error_code": ErrorCode.DEPENDENCY_NOT_FOUND},
        )

        # Call the function under test
        with pytest.raises(ResourceError) as excinfo:
            list_available_versions(dependency="org.example:library", version="1.0.0")

        # Verify the error message
        assert "not found in Maven Central" in str(excinfo.value)

    @patch("mvn_mcp_server.tools.list_available_versions.maven_api")
    @patch("mvn_mcp_server.tools.list_available_versions.version_service")
    def test_unexpected_error(self, mock_version_service, mock_maven_api):
        """Test handling of unexpected errors."""
        # Mock the API to raise an unexpected exception
        mock_maven_api.check_artifact_exists.side_effect = Exception(
            "Unexpected internal error"
        )

        # Call the function under test
        with pytest.raises(ToolError) as excinfo:
            list_available_versions(dependency="org.example:library", version="1.0.0")

        # Verify the error message
        assert "Unexpected error" in str(excinfo.value)
