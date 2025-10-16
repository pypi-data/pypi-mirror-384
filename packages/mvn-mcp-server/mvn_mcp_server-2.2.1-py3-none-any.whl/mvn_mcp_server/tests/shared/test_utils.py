"""Tests for utility functions.

This module tests the utility functions in the mvn_mcp_server.shared.utils module.
"""

import pytest
from fastmcp.exceptions import ValidationError

from mvn_mcp_server.shared.utils import (
    validate_maven_dependency,
    validate_version_string,
    determine_packaging,
    format_error_response,
)
from mvn_mcp_server.shared.data_types import ErrorCode


class TestValidateMavenDependency:
    """Tests for the validate_maven_dependency function."""

    def test_valid_dependency(self):
        """Test with a valid dependency string."""
        group_id, artifact_id = validate_maven_dependency(
            "org.springframework:spring-core"
        )
        assert group_id == "org.springframework"
        assert artifact_id == "spring-core"

    def test_invalid_dependency_format(self):
        """Test with an invalid dependency format."""
        with pytest.raises(ValidationError):
            validate_maven_dependency("org.springframework.spring-core")

    def test_invalid_dependency_empty(self):
        """Test with an empty dependency string."""
        with pytest.raises(ValidationError):
            validate_maven_dependency("")

    def test_invalid_dependency_too_many_parts(self):
        """Test with a dependency string that has too many parts."""
        with pytest.raises(ValidationError):
            validate_maven_dependency("org.springframework:spring-core:5.3.10")


class TestValidateVersionString:
    """Tests for the validate_version_string function."""

    def test_valid_version(self):
        """Test with valid version strings."""
        assert validate_version_string("1.2.3") == "1.2.3"
        assert validate_version_string("5.3.10") == "5.3.10"
        assert validate_version_string("2.7.0-SNAPSHOT") == "2.7.0-SNAPSHOT"
        assert validate_version_string("1.0.0.Final") == "1.0.0.Final"

    def test_invalid_version_empty(self):
        """Test with an empty version string."""
        with pytest.raises(ValidationError):
            validate_version_string("")

    def test_invalid_version_format(self):
        """Test with an invalid version format."""
        with pytest.raises(ValidationError):
            validate_version_string("version")


class TestDeterminePackaging:
    """Tests for the determine_packaging function."""

    def test_default_packaging(self):
        """Test with default packaging."""
        assert determine_packaging("jar", "spring-core") == "jar"

    def test_specified_packaging(self):
        """Test with specified packaging."""
        assert determine_packaging("war", "spring-core") == "war"

    def test_bom_packaging(self):
        """Test with a BOM artifact."""
        assert determine_packaging("jar", "spring-bom") == "pom"

    def test_dependencies_packaging(self):
        """Test with a dependencies artifact."""
        assert determine_packaging("jar", "spring-dependencies") == "pom"


class TestFormatErrorResponse:
    """Tests for the format_error_response function."""

    def test_basic_error_response(self):
        """Test formatting a basic error response."""
        response = format_error_response(
            ErrorCode.INVALID_INPUT_FORMAT, "Invalid input"
        )
        assert response["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT
        assert response["error"]["message"] == "Invalid input"
        assert "details" not in response["error"]

    def test_error_response_with_details(self):
        """Test formatting an error response with details."""
        details = {"field": "dependency", "issue": "missing groupId"}
        response = format_error_response(
            ErrorCode.INVALID_INPUT_FORMAT, "Invalid input", details
        )
        assert response["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT
        assert response["error"]["message"] == "Invalid input"
        assert response["error"]["details"] == details
