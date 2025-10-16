"""Tests for the maven_api service."""

import unittest
from unittest.mock import Mock, patch

from mvn_mcp_server.services.maven_api import MavenApiService
from mvn_mcp_server.services.cache import MavenCache
from fastmcp.exceptions import ResourceError


class TestMavenApiService(unittest.TestCase):
    """Test cases for the MavenApiService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = MavenCache()
        self.api_service = MavenApiService(self.cache)

    @patch("requests.get")
    def test_fetch_artifact_metadata(self, mock_get):
        """Test fetching artifact metadata."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <metadata>
            <groupId>org.example</groupId>
            <artifactId>test-artifact</artifactId>
            <versioning>
                <latest>2.0.0</latest>
                <release>1.9.0</release>
                <versions>
                    <version>1.0.0</version>
                    <version>1.9.0</version>
                    <version>2.0.0</version>
                </versions>
            </versioning>
        </metadata>
        """
        mock_get.return_value = mock_response

        # Call the method
        metadata = self.api_service.fetch_artifact_metadata(
            "org.example", "test-artifact"
        )

        # Verify the result
        self.assertEqual(metadata["group_id"], "org.example")
        self.assertEqual(metadata["artifact_id"], "test-artifact")
        self.assertEqual(metadata["latest_version"], "2.0.0")
        self.assertEqual(metadata["release_version"], "1.9.0")
        self.assertEqual(metadata["versions"], ["1.0.0", "1.9.0", "2.0.0"])

        # Verify the request
        mock_get.assert_called_once_with(
            "https://repo1.maven.org/maven2/org/example/test-artifact/maven-metadata.xml",
            timeout=10,
        )

    @patch("requests.get")
    def test_fetch_artifact_metadata_not_found(self, mock_get):
        """Test fetching artifact metadata for nonexistent artifact."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the method and check for exception
        with self.assertRaises(ResourceError) as context:
            self.api_service.fetch_artifact_metadata("org.nonexistent", "artifact")

        # Verify error message contains "not found"
        self.assertIn("not found", str(context.exception))

    @patch("requests.head")
    def test_check_artifact_exists_direct_success(self, mock_head):
        """Test checking artifact existence with direct hit."""
        # Mock response for direct check
        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head.return_value = mock_head_response

        # Call the method
        exists = self.api_service.check_artifact_exists(
            "org.example", "test-artifact", "1.0.0"
        )

        # Verify the result
        self.assertTrue(exists)

        # Verify the request
        mock_head.assert_called_once_with(
            "https://repo1.maven.org/maven2/org/example/test-artifact/1.0.0/test-artifact-1.0.0.jar",
            timeout=10,
        )

    @patch("requests.head")
    @patch(
        "mvn_mcp_server.services.maven_api.MavenApiService._check_version_in_metadata"
    )
    def test_check_artifact_exists_fallback(self, mock_check_metadata, mock_head):
        """Test checking artifact existence with fallback to metadata."""
        # Mock response for direct check (not found)
        mock_head_response = Mock()
        mock_head_response.status_code = 404
        mock_head.return_value = mock_head_response

        # Mock metadata check (found)
        mock_check_metadata.return_value = True

        # Call the method
        exists = self.api_service.check_artifact_exists(
            "org.example", "test-artifact", "1.0.0"
        )

        # Verify the result
        self.assertTrue(exists)

        # Verify both methods were called
        mock_head.assert_called_once()
        mock_check_metadata.assert_called_once_with(
            "org.example", "test-artifact", "1.0.0"
        )

    @patch("mvn_mcp_server.services.maven_api.MavenApiService.fetch_artifact_metadata")
    def test_get_all_versions(self, mock_fetch_metadata):
        """Test getting all versions."""
        # Mock metadata response
        mock_fetch_metadata.return_value = {
            "group_id": "org.example",
            "artifact_id": "test-artifact",
            "latest_version": "2.0.0",
            "release_version": "1.9.0",
            "versions": ["1.0.0", "1.9.0", "2.0.0"],
        }

        # Call the method
        versions = self.api_service.get_all_versions("org.example", "test-artifact")

        # Verify the result
        self.assertEqual(versions, ["1.0.0", "1.9.0", "2.0.0"])

        # Verify fetch_metadata was called
        mock_fetch_metadata.assert_called_once_with("org.example", "test-artifact")

    @patch("mvn_mcp_server.services.maven_api.MavenApiService.fetch_artifact_metadata")
    def test_get_all_versions_empty(self, mock_fetch_metadata):
        """Test getting all versions when no versions are available."""
        # Mock metadata response with no versions
        mock_fetch_metadata.return_value = {
            "group_id": "org.example",
            "artifact_id": "test-artifact",
            "latest_version": None,
            "release_version": None,
            "versions": [],
        }

        # Call the method and check for exception
        with self.assertRaises(ResourceError):
            self.api_service.get_all_versions("org.example", "test-artifact")

        # Just verify that a ResourceError was raised - specific message is implementation detail

    @patch("requests.get")
    def test_search_artifacts(self, mock_get):
        """Test searching artifacts."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "numFound": 3,
                "docs": [
                    {"g": "org.example", "a": "test1", "v": "1.0.0"},
                    {"g": "org.example", "a": "test2", "v": "2.0.0"},
                    {"g": "org.example", "a": "test3", "v": "3.0.0"},
                ],
            }
        }
        mock_get.return_value = mock_response

        # Call the method
        data, error = self.api_service.search_artifacts("org.example")

        # Verify the result
        self.assertIsNone(error)
        self.assertEqual(data["response"]["numFound"], 3)
        self.assertEqual(len(data["response"]["docs"]), 3)

        # Verify request parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://search.maven.org/solrsearch/select")
        self.assertEqual(kwargs["params"]["q"], "org.example")
        self.assertEqual(kwargs["params"]["core"], "gav")

    @patch("mvn_mcp_server.services.maven_api.MavenApiService.fetch_artifact_metadata")
    def test_get_latest_version_from_release(self, mock_fetch_metadata):
        """Test getting latest version when release version is available."""
        # Mock metadata response
        mock_fetch_metadata.return_value = {
            "group_id": "org.example",
            "artifact_id": "test-artifact",
            "latest_version": "2.0.0-SNAPSHOT",
            "release_version": "1.9.0",
            "versions": ["1.0.0", "1.9.0", "2.0.0-SNAPSHOT"],
        }

        # Call the method
        version = self.api_service.get_latest_version("org.example", "test-artifact")

        # Verify the result (should be release version, not snapshot)
        self.assertEqual(version, "1.9.0")

        # Verify fetch_metadata was called
        mock_fetch_metadata.assert_called_once_with("org.example", "test-artifact")

    @patch("mvn_mcp_server.services.maven_api.MavenApiService.fetch_artifact_metadata")
    @patch("mvn_mcp_server.services.maven_api.MavenApiService.check_artifact_exists")
    def test_get_latest_version_with_classifier(
        self, mock_check_exists, mock_fetch_metadata
    ):
        """Test getting latest version with classifier."""
        # Mock metadata response
        mock_fetch_metadata.return_value = {
            "group_id": "org.example",
            "artifact_id": "test-artifact",
            "latest_version": "2.0.0",
            "release_version": "1.9.0",
            "versions": ["1.0.0", "1.9.0", "2.0.0"],
        }

        # Mock artifact existence checks
        # The release version doesn't have the classifier
        mock_check_exists.side_effect = [
            False,  # For release version (1.9.0)
            True,  # For latest version (2.0.0)
        ]

        # Call the method
        version = self.api_service.get_latest_version(
            "org.example", "test-artifact", classifier="sources"
        )

        # Verify the result (should be latest version since release lacks classifier)
        self.assertEqual(version, "2.0.0")

        # Verify check_artifact_exists was called twice
        self.assertEqual(mock_check_exists.call_count, 2)
