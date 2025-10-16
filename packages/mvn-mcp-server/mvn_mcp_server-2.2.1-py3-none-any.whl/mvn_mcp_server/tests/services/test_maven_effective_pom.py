"""Tests for Maven Effective POM Service.

This module tests the Maven effective POM generation functionality
for profile-based dependency resolution.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastmcp.exceptions import ResourceError
from mvn_mcp_server.services.maven_effective_pom import MavenEffectivePomService


class TestMavenAvailability:
    """Tests for Maven availability checking."""

    @patch("subprocess.run")
    def test_maven_available_success(self, mock_run):
        """Test successful Maven availability check."""
        # Mock successful Maven version check
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Apache Maven 3.9.11"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = MavenEffectivePomService.check_maven_availability()

        assert result is True
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["mvn", "--version"]

    @patch("subprocess.run")
    def test_maven_not_found(self, mock_run):
        """Test Maven not found on system."""
        mock_run.side_effect = FileNotFoundError()

        result = MavenEffectivePomService.check_maven_availability()

        assert result is False

    @patch("subprocess.run")
    def test_maven_check_failed(self, mock_run):
        """Test Maven check returns non-zero exit code."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Maven error"
        mock_run.return_value = mock_process

        result = MavenEffectivePomService.check_maven_availability()

        assert result is False

    @patch("subprocess.run")
    def test_maven_check_timeout(self, mock_run):
        """Test Maven check timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("mvn", 10)

        result = MavenEffectivePomService.check_maven_availability()

        assert result is False

    @patch("subprocess.run")
    def test_maven_check_unexpected_error(self, mock_run):
        """Test unexpected error during Maven check."""
        mock_run.side_effect = Exception("Unexpected error")

        result = MavenEffectivePomService.check_maven_availability()

        assert result is False


class TestEffectivePomGeneration:
    """Tests for effective POM generation."""

    @pytest.fixture
    def mock_workspace(self, tmp_path):
        """Create a temporary workspace with a POM file."""
        workspace = tmp_path / "test-project"
        workspace.mkdir()

        # Create a simple POM file
        pom_content = """<?xml version="1.0"?>
        <project>
            <groupId>com.example</groupId>
            <artifactId>test-project</artifactId>
            <version>1.0.0</version>
        </project>"""

        pom_file = workspace / "pom.xml"
        with open(pom_file, "w") as f:
            f.write(pom_content)

        return workspace

    @patch("subprocess.run")
    def test_generate_effective_pom_single_profile(
        self, mock_run, mock_workspace, tmp_path
    ):
        """Test generating effective POM for a single profile."""
        # Create explicit output file
        output_file = tmp_path / "effective-pom-azure.xml"
        output_file.write_text("<?xml version='1.0'?><project></project>")

        # Mock successful Maven execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "[INFO] Effective POM generated"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Execute with explicit output file
        result = MavenEffectivePomService.generate_effective_pom(
            mock_workspace, ["azure"], output_file=output_file
        )

        # Verify
        assert result == output_file
        assert result.exists()
        assert mock_run.called

        # Verify Maven command
        args = mock_run.call_args[0][0]
        assert "mvn" in args
        assert "help:effective-pom" in args
        assert "-Pazure" in args

    @patch("subprocess.run")
    def test_generate_effective_pom_multiple_profiles(
        self, mock_run, mock_workspace, tmp_path
    ):
        """Test generating effective POM for multiple profiles."""
        # Create explicit output file
        output_file = tmp_path / "effective-pom-azure-aws.xml"
        output_file.write_text("<?xml version='1.0'?><project></project>")

        # Mock successful Maven execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "[INFO] Effective POM generated"
        mock_run.return_value = mock_process

        # Execute with explicit output file
        MavenEffectivePomService.generate_effective_pom(
            mock_workspace, ["azure", "aws"], output_file=output_file
        )

        # Verify Maven command has both profiles
        args = mock_run.call_args[0][0]
        assert "-Pazure,aws" in args

    @patch("subprocess.run")
    def test_generate_effective_pom_workspace_not_found(self, mock_run):
        """Test error when workspace doesn't exist."""
        with pytest.raises(ResourceError) as exc_info:
            MavenEffectivePomService.generate_effective_pom(
                Path("/nonexistent/path"), ["azure"]
            )

        assert "does not exist" in str(exc_info.value)

    @patch("subprocess.run")
    def test_generate_effective_pom_no_pom_file(self, mock_run, tmp_path):
        """Test error when pom.xml doesn't exist."""
        workspace = tmp_path / "no-pom-project"
        workspace.mkdir()

        with pytest.raises(ResourceError) as exc_info:
            MavenEffectivePomService.generate_effective_pom(workspace, ["azure"])

        assert "No pom.xml found" in str(exc_info.value)

    @patch("subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    def test_generate_effective_pom_maven_failure(
        self, mock_temp_file, mock_run, mock_workspace
    ):
        """Test handling of Maven execution failure."""
        # Mock temp file
        temp_file_path = mock_workspace / "effective-pom.xml"
        mock_temp_file.return_value.__enter__.return_value.name = str(temp_file_path)

        # Mock Maven failure
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "[ERROR] Unknown profile: invalid"
        mock_run.return_value = mock_process

        with pytest.raises(ResourceError) as exc_info:
            MavenEffectivePomService.generate_effective_pom(mock_workspace, ["invalid"])

        assert "Unknown profile" in str(exc_info.value)

    @patch("subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    def test_generate_effective_pom_timeout(
        self, mock_temp_file, mock_run, mock_workspace
    ):
        """Test handling of Maven timeout."""
        import subprocess

        # Mock temp file
        temp_file_path = mock_workspace / "effective-pom.xml"
        mock_temp_file.return_value.__enter__.return_value.name = str(temp_file_path)

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("mvn", 60)

        with pytest.raises(ResourceError) as exc_info:
            MavenEffectivePomService.generate_effective_pom(mock_workspace, ["azure"])

        assert "timed out" in str(exc_info.value)

    @patch("subprocess.run")
    def test_generate_effective_pom_empty_output(
        self, mock_run, mock_workspace, tmp_path
    ):
        """Test error when Maven creates empty output file."""
        # Create empty output file (0 bytes)
        output_file = tmp_path / "effective-pom.xml"
        output_file.touch()

        # Mock successful Maven execution (but file is empty)
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        with pytest.raises(ResourceError) as exc_info:
            MavenEffectivePomService.generate_effective_pom(
                mock_workspace, ["azure"], output_file=output_file
            )

        assert "empty" in str(exc_info.value).lower()


class TestBatchProfileProcessing:
    """Tests for batch profile processing."""

    @pytest.fixture
    def mock_workspace(self, tmp_path):
        """Create a temporary workspace with a POM file."""
        workspace = tmp_path / "test-project"
        workspace.mkdir()

        pom_content = """<?xml version="1.0"?>
        <project>
            <groupId>com.example</groupId>
            <artifactId>test-project</artifactId>
            <version>1.0.0</version>
        </project>"""

        pom_file = workspace / "pom.xml"
        with open(pom_file, "w") as f:
            f.write(pom_content)

        return workspace

    @patch(
        "mvn_mcp_server.services.maven_effective_pom.MavenEffectivePomService.generate_effective_pom"
    )
    def test_generate_effective_poms_for_multiple_profiles(
        self, mock_generate, mock_workspace
    ):
        """Test generating effective POMs for multiple profiles."""

        # Mock individual POM generation
        def mock_gen(workspace, profiles):
            profile_name = profiles[0]
            return mock_workspace / f"effective-pom-{profile_name}.xml"

        mock_generate.side_effect = mock_gen

        # Execute
        result = MavenEffectivePomService.generate_effective_poms_for_profiles(
            mock_workspace, ["azure", "aws", "ibm"]
        )

        # Verify
        assert len(result) == 3
        assert "azure" in result
        assert "aws" in result
        assert "ibm" in result
        assert mock_generate.call_count == 3

    @patch(
        "mvn_mcp_server.services.maven_effective_pom.MavenEffectivePomService.generate_effective_pom"
    )
    def test_generate_effective_poms_with_failure(self, mock_generate, mock_workspace):
        """Test handling when one profile fails."""

        # Mock: azure succeeds, aws fails, ibm succeeds
        def mock_gen(workspace, profiles):
            profile_name = profiles[0]
            if profile_name == "aws":
                raise ResourceError(f"Unknown profile: {profile_name}")
            return mock_workspace / f"effective-pom-{profile_name}.xml"

        mock_generate.side_effect = mock_gen

        # Should raise error with details about the failed profile
        with pytest.raises(ResourceError) as exc_info:
            MavenEffectivePomService.generate_effective_poms_for_profiles(
                mock_workspace, ["azure", "aws", "ibm"]
            )

        assert "aws" in str(exc_info.value)
        assert "Unknown profile" in str(exc_info.value)


class TestCleanup:
    """Tests for cleanup functionality."""

    def test_cleanup_effective_poms(self, tmp_path):
        """Test cleanup of temporary effective POM files."""
        # Create some temporary files
        pom1 = tmp_path / "effective-pom-azure.xml"
        pom2 = tmp_path / "effective-pom-aws.xml"
        pom1.write_text("<project></project>")
        pom2.write_text("<project></project>")

        effective_poms = {
            "azure": pom1,
            "aws": pom2,
        }

        # Execute cleanup
        MavenEffectivePomService.cleanup_effective_poms(effective_poms)

        # Verify files are deleted
        assert not pom1.exists()
        assert not pom2.exists()

    def test_cleanup_nonexistent_files(self, tmp_path):
        """Test cleanup handles non-existent files gracefully."""
        pom1 = tmp_path / "nonexistent.xml"

        effective_poms = {"azure": pom1}

        # Should not raise error
        MavenEffectivePomService.cleanup_effective_poms(effective_poms)
