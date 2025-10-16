"""Tests for Java security scanning tool.

This module tests the Java security scanning tool for Maven projects.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, mock_open

from mvn_mcp_server.tools.java_security_scan import (
    scan_java_project,
    check_trivy_availability,
)


class TestJavaSecurityScan:
    """Tests for the scan_java_project function."""

    @pytest.fixture
    def mock_workspace(self, tmp_path):
        """Create a temporary workspace with a POM file."""
        # Create a temporary directory
        workspace = tmp_path / "test-java-project"
        workspace.mkdir()

        # Create a dummy POM file
        pom_content = """<project>
            <groupId>com.example</groupId>
            <artifactId>test-project</artifactId>
            <version>1.0.0</version>
        </project>"""

        pom_path = workspace / "pom.xml"
        with open(pom_path, "w") as f:
            f.write(pom_content)

        return workspace

    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("os.unlink")  # Add patch for os.unlink
    @patch("tempfile.NamedTemporaryFile")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_trivy_scan(
        self,
        mock_open_file,
        mock_run,
        mock_temp_file,
        mock_unlink,
        mock_check_trivy,
        mock_maven_service,
        mock_workspace,
    ):
        """Test Trivy scanning."""
        # Set up mocks
        mock_check_trivy.return_value = True
        mock_maven_service.check_maven_availability.return_value = (
            False  # No profiles, so Maven not needed
        )

        # Mock the temp file
        temp_file_name = "/tmp/trivy_results.json"
        mock_temp_file.return_value.__enter__.return_value.name = temp_file_name

        # Mock subprocess execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Mock Trivy JSON response
        trivy_json_response = {
            "Results": [
                {
                    "Target": "pom.xml",
                    "Class": "lang-pkgs",
                    "Type": "pom",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-44228",
                            "PkgID": "org.apache.logging.log4j:log4j-core:2.14.1",
                            "PkgName": "org.apache.logging.log4j:log4j-core",
                            "InstalledVersion": "2.14.1",
                            "FixedVersion": "2.17.1",
                            "Severity": "CRITICAL",
                            "Description": "Log4Shell vulnerability",
                            "References": [
                                {
                                    "URL": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        # Configure the mock_open to work correctly with the explicit filename
        mock_open_file.return_value.__enter__.return_value.read.return_value = (
            json.dumps(trivy_json_response)
        )

        # Execute the function
        result = scan_java_project(str(mock_workspace))

        # Check the result
        assert result["status"] == "success"
        assert result["result"]["scan_mode"] == "trivy"
        assert result["result"]["vulnerabilities_found"] is True
        assert result["result"]["total_vulnerabilities"] == 1
        assert len(result["result"]["modules_scanned"]) == 1
        assert result["result"]["severity_counts"]["critical"] == 1
        assert (
            "scan_limitations" not in result["result"]
            or result["result"]["scan_limitations"] is None
        )

        # Verify mock calls
        mock_check_trivy.assert_called_once()
        mock_run.assert_called_once()
        mock_open_file.assert_called_with(temp_file_name, "r")

        # Verify Trivy command arguments
        args, kwargs = mock_run.call_args
        trivy_cmd = args[0]
        assert "trivy" in trivy_cmd
        assert "fs" in trivy_cmd
        assert "--security-checks" in trivy_cmd
        assert "vuln" in trivy_cmd
        assert "--format" in trivy_cmd
        assert "json" in trivy_cmd

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    def test_trivy_not_available(self, mock_check_trivy, mock_workspace):
        """Test handling when Trivy is not available."""
        # Set up mock
        mock_check_trivy.return_value = False

        # Execute the function and check for ResourceError in the response
        result = scan_java_project(str(mock_workspace))

        assert result["status"] == "error"
        assert result["error"]["code"] == "TRIVY_ERROR"
        assert "Trivy is not available" in result["error"]["message"]

    def test_invalid_workspace(self):
        """Test with an invalid workspace path."""
        result = scan_java_project("/path/that/does/not/exist")

        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT_FORMAT"

    def test_not_maven_project(self, tmp_path):
        """Test with a directory that is not a Maven project."""
        workspace = tmp_path / "not-maven"
        workspace.mkdir()

        result = scan_java_project(str(workspace))

        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT_FORMAT"
        assert "pom.xml" in result["error"]["message"]


class TestHelperFunctions:
    """Tests for helper functions in the java_security_scan module."""

    @patch("subprocess.run")
    def test_trivy_availability_check(self, mock_run):
        """Test checking Trivy availability."""
        # Trivy available
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        assert check_trivy_availability() is True

        # Trivy not available
        mock_process.returncode = 1
        assert check_trivy_availability() is False

        # Trivy not found
        mock_run.side_effect = FileNotFoundError()
        assert check_trivy_availability() is False


class TestProfileBasedScanning:
    """Tests for profile-based security scanning."""

    @pytest.fixture
    def mock_workspace(self, tmp_path):
        """Create a temporary workspace with a POM file."""
        workspace = tmp_path / "test-profile-project"
        workspace.mkdir()

        pom_content = """<?xml version="1.0"?>
        <project>
            <groupId>com.example</groupId>
            <artifactId>test-project</artifactId>
            <version>1.0.0</version>
            <profiles>
                <profile><id>azure</id></profile>
                <profile><id>aws</id></profile>
            </profiles>
        </project>"""

        pom_file = workspace / "pom.xml"
        with open(pom_file, "w") as f:
            f.write(pom_content)

        return workspace

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    @patch("mvn_mcp_server.tools.java_security_scan._run_trivy_scan")
    def test_profile_scan_with_maven_available(
        self,
        mock_trivy_scan,
        mock_maven_service,
        mock_check_trivy,
        mock_workspace,
        tmp_path,
    ):
        """Test profile scanning when Maven is available."""
        # Set up mocks
        mock_check_trivy.return_value = True
        mock_maven_service.check_maven_availability.return_value = True

        # Mock effective POM generation
        azure_pom = tmp_path / "effective-azure.xml"
        aws_pom = tmp_path / "effective-aws.xml"
        azure_pom.write_text("<project></project>")
        aws_pom.write_text("<project></project>")

        mock_maven_service.generate_effective_poms_for_profiles.return_value = {
            "azure": azure_pom,
            "aws": aws_pom,
        }

        # Mock Trivy scan results (different vulnerabilities per profile)
        def mock_trivy_side_effect(pom_path):
            if "azure" in str(pom_path):
                return {
                    "Results": [
                        {
                            "Target": "pom.xml",
                            "Vulnerabilities": [
                                {
                                    "VulnerabilityID": "CVE-2024-0001",
                                    "PkgID": "com.azure:azure-core:1.0.0",
                                    "Severity": "HIGH",
                                    "Description": "Azure vuln",
                                    "FixedVersion": "1.1.0",
                                    "References": [],
                                }
                            ],
                        }
                    ]
                }
            else:  # aws
                return {
                    "Results": [
                        {
                            "Target": "pom.xml",
                            "Vulnerabilities": [
                                {
                                    "VulnerabilityID": "CVE-2024-0002",
                                    "PkgID": "com.amazonaws:aws-java-sdk:1.0.0",
                                    "Severity": "CRITICAL",
                                    "Description": "AWS vuln",
                                    "FixedVersion": "1.1.0",
                                    "References": [],
                                }
                            ],
                        }
                    ]
                }

        mock_trivy_scan.side_effect = mock_trivy_side_effect

        # Execute with profiles
        result = scan_java_project(
            str(mock_workspace), include_profiles=["azure", "aws"]
        )

        # Verify success
        assert result["status"] == "success"
        assert result["result"]["scan_mode"] == "profile-effective"
        assert result["result"]["maven_available"] is True

        # Verify per-profile results exist
        assert "per_profile_results" in result["result"]
        assert result["result"]["per_profile_results"] is not None
        assert "azure" in result["result"]["per_profile_results"]
        assert "aws" in result["result"]["per_profile_results"]

        # Verify effective POMs were generated
        mock_maven_service.generate_effective_poms_for_profiles.assert_called_once_with(
            mock_workspace, ["azure", "aws"]
        )

        # Verify cleanup was called
        mock_maven_service.cleanup_effective_poms.assert_called_once()

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    @patch("os.unlink")
    @patch("tempfile.NamedTemporaryFile")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_profile_scan_maven_unavailable_fallback(
        self,
        mock_open_file,
        mock_run,
        mock_temp_file,
        mock_unlink,
        mock_maven_service,
        mock_check_trivy,
        mock_workspace,
    ):
        """Test fallback to workspace scan when profiles specified but Maven unavailable."""
        # Set up mocks
        mock_check_trivy.return_value = True
        mock_maven_service.check_maven_availability.return_value = (
            False  # Maven not available
        )

        # Mock temp file
        temp_file_name = "/tmp/trivy_results.json"
        mock_temp_file.return_value.__enter__.return_value.name = temp_file_name

        # Mock subprocess (Trivy only, no Maven)
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Mock Trivy response
        trivy_json_response = {"Results": []}
        mock_open_file.return_value.__enter__.return_value.read.return_value = (
            json.dumps(trivy_json_response)
        )

        # Execute with profiles but Maven unavailable
        result = scan_java_project(str(mock_workspace), include_profiles=["azure"])

        # Verify fallback to workspace scanning
        assert result["status"] == "success"
        assert result["result"]["scan_mode"] == "trivy"  # Not "profile-effective"
        assert result["result"]["maven_available"] is False

        # Verify limitation message
        assert result["result"]["scan_limitations"] is not None
        assert len(result["result"]["scan_limitations"]) > 0
        assert any("Maven" in lim for lim in result["result"]["scan_limitations"])

        # Verify no profile results
        assert result["result"]["per_profile_results"] is None

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    @patch("mvn_mcp_server.tools.java_security_scan._run_trivy_scan")
    def test_cross_profile_vulnerability_analysis(
        self,
        mock_trivy_scan,
        mock_maven_service,
        mock_check_trivy,
        mock_workspace,
        tmp_path,
    ):
        """Test cross-profile vulnerability analysis."""
        # Set up mocks
        mock_check_trivy.return_value = True
        mock_maven_service.check_maven_availability.return_value = True

        # Mock effective POM generation for 3 profiles
        azure_pom = tmp_path / "effective-azure.xml"
        aws_pom = tmp_path / "effective-aws.xml"
        ibm_pom = tmp_path / "effective-ibm.xml"
        azure_pom.write_text("<project></project>")
        aws_pom.write_text("<project></project>")
        ibm_pom.write_text("<project></project>")

        mock_maven_service.generate_effective_poms_for_profiles.return_value = {
            "azure": azure_pom,
            "aws": aws_pom,
            "ibm": ibm_pom,
        }

        # Mock Trivy results:
        # - CVE-COMMON appears in all 3 profiles
        # - CVE-AZURE-ONLY appears only in azure
        # - CVE-AWS-ONLY appears only in aws
        def mock_trivy_side_effect(pom_path):
            path_str = str(pom_path)
            vulns = [
                {
                    "VulnerabilityID": "CVE-COMMON",
                    "PkgID": "org.springframework:spring-core:5.0.0",
                    "Severity": "HIGH",
                    "Description": "Common vuln",
                    "FixedVersion": "5.3.0",
                    "References": [],
                }
            ]

            if "azure" in path_str:
                vulns.append(
                    {
                        "VulnerabilityID": "CVE-AZURE-ONLY",
                        "PkgID": "com.azure:azure-core:1.0.0",
                        "Severity": "MEDIUM",
                        "Description": "Azure specific",
                        "FixedVersion": "1.1.0",
                        "References": [],
                    }
                )
            elif "aws" in path_str:
                vulns.append(
                    {
                        "VulnerabilityID": "CVE-AWS-ONLY",
                        "PkgID": "com.amazonaws:aws-sdk:1.0.0",
                        "Severity": "MEDIUM",
                        "Description": "AWS specific",
                        "FixedVersion": "1.1.0",
                        "References": [],
                    }
                )

            return {"Results": [{"Target": "pom.xml", "Vulnerabilities": vulns}]}

        mock_trivy_scan.side_effect = mock_trivy_side_effect

        # Execute with multiple profiles
        result = scan_java_project(
            str(mock_workspace), include_profiles=["azure", "aws", "ibm"]
        )

        # Verify success
        assert result["status"] == "success"
        assert result["result"]["scan_mode"] == "profile-effective"

        # Verify cross-profile analysis
        assert "profile_specific_vulnerabilities" in result["result"]
        analysis = result["result"]["profile_specific_vulnerabilities"]

        assert "CVE-COMMON" in analysis["common_to_all_profiles"]
        assert "CVE-AZURE-ONLY" in analysis["profile_specific_cves"]["azure_only"]
        assert "CVE-AWS-ONLY" in analysis["profile_specific_cves"]["aws_only"]

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    def test_profile_scan_maven_error_handling(
        self, mock_maven_service, mock_check_trivy, mock_workspace
    ):
        """Test error handling when Maven fails during profile scanning."""
        # Set up mocks
        mock_check_trivy.return_value = True
        mock_maven_service.check_maven_availability.return_value = True

        # Mock Maven failure
        from fastmcp.exceptions import ResourceError

        mock_maven_service.generate_effective_poms_for_profiles.side_effect = (
            ResourceError("Maven effective-pom generation failed")
        )

        # Execute with profiles
        result = scan_java_project(str(mock_workspace), include_profiles=["azure"])

        # Verify error is properly handled
        assert result["status"] == "error"
        assert "maven" in result["error"]["message"].lower()

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    @patch("mvn_mcp_server.tools.java_security_scan._run_trivy_scan")
    def test_profile_scan_single_profile(
        self,
        mock_trivy_scan,
        mock_maven_service,
        mock_check_trivy,
        mock_workspace,
        tmp_path,
    ):
        """Test scanning a single profile."""
        # Set up mocks
        mock_check_trivy.return_value = True
        mock_maven_service.check_maven_availability.return_value = True

        # Mock effective POM generation for single profile
        azure_pom = tmp_path / "effective-azure.xml"
        azure_pom.write_text("<project></project>")

        mock_maven_service.generate_effective_poms_for_profiles.return_value = {
            "azure": azure_pom
        }

        # Mock Trivy result
        mock_trivy_scan.return_value = {
            "Results": [
                {
                    "Target": "pom.xml",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-1234",
                            "PkgID": "com.azure:azure-core:1.0.0",
                            "Severity": "HIGH",
                            "Description": "Test vulnerability",
                            "FixedVersion": "1.1.0",
                            "References": [],
                        }
                    ],
                }
            ]
        }

        # Execute with single profile
        result = scan_java_project(str(mock_workspace), include_profiles=["azure"])

        # Verify success
        assert result["status"] == "success"
        assert result["result"]["scan_mode"] == "profile-effective"
        assert len(result["result"]["per_profile_results"]) == 1
        assert "azure" in result["result"]["per_profile_results"]

        # Verify profile result structure
        azure_result = result["result"]["per_profile_results"]["azure"]
        assert azure_result["profile_id"] == "azure"
        assert azure_result["effective_pom_used"] is True
        assert azure_result["vulnerabilities_found"] is True
        assert azure_result["total_vulnerabilities"] == 1

        # Verify cleanup
        mock_maven_service.cleanup_effective_poms.assert_called_once()


class TestProfileAggregationFunctions:
    """Tests for profile aggregation and analysis helper functions."""

    def test_analyze_profile_specificity_all_common(self):
        """Test when all CVEs are common to all profiles."""
        from mvn_mcp_server.tools.java_security_scan import _analyze_profile_specificity
        from mvn_mcp_server.shared.data_types import JavaVulnerability

        # Create mock vulnerabilities - same CVE in all profiles
        common_vuln = JavaVulnerability(
            module="test",
            group_id="org.springframework",
            artifact_id="spring-core",
            installed_version="5.0.0",
            vulnerability_id="CVE-COMMON",
            cve_id="CVE-COMMON",
            severity="high",
            description="Common vuln",
            recommendation="5.3.0",
            in_profile=None,
            direct_dependency=True,
            is_in_bom=False,
            version_source="direct",
            source_location="pom.xml",
            links=[],
            fix_available=True,
        )

        profile_results = {
            "azure": {"vulnerabilities": [common_vuln]},
            "aws": {"vulnerabilities": [common_vuln]},
            "ibm": {"vulnerabilities": [common_vuln]},
        }

        result = _analyze_profile_specificity(profile_results)

        assert len(result.common_to_all_profiles) == 1
        assert "CVE-COMMON" in result.common_to_all_profiles
        assert len(result.profile_specific_cves) == 0

    def test_analyze_profile_specificity_all_unique(self):
        """Test when all CVEs are unique to their profiles."""
        from mvn_mcp_server.tools.java_security_scan import _analyze_profile_specificity
        from mvn_mcp_server.shared.data_types import JavaVulnerability

        # Create unique vulnerabilities for each profile
        azure_vuln = JavaVulnerability(
            module="test",
            group_id="com.azure",
            artifact_id="azure-core",
            installed_version="1.0.0",
            vulnerability_id="CVE-AZURE",
            cve_id="CVE-AZURE",
            severity="high",
            description="Azure vuln",
            recommendation="1.1.0",
            in_profile="azure",
            direct_dependency=True,
            is_in_bom=False,
            version_source="direct",
            source_location="pom.xml",
            links=[],
            fix_available=True,
        )

        aws_vuln = JavaVulnerability(
            module="test",
            group_id="com.amazonaws",
            artifact_id="aws-sdk",
            installed_version="1.0.0",
            vulnerability_id="CVE-AWS",
            cve_id="CVE-AWS",
            severity="high",
            description="AWS vuln",
            recommendation="1.1.0",
            in_profile="aws",
            direct_dependency=True,
            is_in_bom=False,
            version_source="direct",
            source_location="pom.xml",
            links=[],
            fix_available=True,
        )

        profile_results = {
            "azure": {"vulnerabilities": [azure_vuln]},
            "aws": {"vulnerabilities": [aws_vuln]},
        }

        result = _analyze_profile_specificity(profile_results)

        assert len(result.common_to_all_profiles) == 0
        assert "azure_only" in result.profile_specific_cves
        assert "aws_only" in result.profile_specific_cves
        assert "CVE-AZURE" in result.profile_specific_cves["azure_only"]
        assert "CVE-AWS" in result.profile_specific_cves["aws_only"]

    def test_analyze_profile_specificity_mixed(self):
        """Test mixed scenario with both common and unique CVEs."""
        from mvn_mcp_server.tools.java_security_scan import _analyze_profile_specificity
        from mvn_mcp_server.shared.data_types import JavaVulnerability

        # Common vulnerability
        common_vuln = JavaVulnerability(
            module="test",
            group_id="org.springframework",
            artifact_id="spring-core",
            installed_version="5.0.0",
            vulnerability_id="CVE-COMMON",
            cve_id="CVE-COMMON",
            severity="high",
            description="Common",
            recommendation="5.3.0",
            in_profile=None,
            direct_dependency=True,
            is_in_bom=False,
            version_source="direct",
            source_location="pom.xml",
            links=[],
            fix_available=True,
        )

        # Azure-specific vulnerability
        azure_vuln = JavaVulnerability(
            module="test",
            group_id="com.azure",
            artifact_id="azure-core",
            installed_version="1.0.0",
            vulnerability_id="CVE-AZURE",
            cve_id="CVE-AZURE",
            severity="medium",
            description="Azure",
            recommendation="1.1.0",
            in_profile="azure",
            direct_dependency=True,
            is_in_bom=False,
            version_source="direct",
            source_location="pom.xml",
            links=[],
            fix_available=True,
        )

        profile_results = {
            "azure": {"vulnerabilities": [common_vuln, azure_vuln]},
            "aws": {"vulnerabilities": [common_vuln]},
        }

        result = _analyze_profile_specificity(profile_results)

        assert len(result.common_to_all_profiles) == 1
        assert "CVE-COMMON" in result.common_to_all_profiles
        assert "azure_only" in result.profile_specific_cves
        assert "CVE-AZURE" in result.profile_specific_cves["azure_only"]

    def test_analyze_profile_specificity_empty_profiles(self):
        """Test with profiles that have no vulnerabilities."""
        from mvn_mcp_server.tools.java_security_scan import _analyze_profile_specificity

        profile_results = {
            "azure": {"vulnerabilities": []},
            "aws": {"vulnerabilities": []},
        }

        result = _analyze_profile_specificity(profile_results)

        assert len(result.common_to_all_profiles) == 0
        assert len(result.profile_specific_cves) == 0

    def test_aggregate_profile_results_pagination(self):
        """Test aggregation with pagination."""
        from mvn_mcp_server.tools.java_security_scan import _aggregate_profile_results
        from mvn_mcp_server.shared.data_types import JavaVulnerability

        # Create vulnerabilities for two profiles
        vulns_azure = []
        vulns_aws = []

        for i in range(5):
            vulns_azure.append(
                JavaVulnerability(
                    module="test",
                    group_id="com.azure",
                    artifact_id="azure-core",
                    installed_version="1.0.0",
                    vulnerability_id=f"CVE-AZURE-{i}",
                    cve_id=f"CVE-AZURE-{i}",
                    severity="high",
                    description=f"Azure vuln {i}",
                    recommendation="1.1.0",
                    in_profile="azure",
                    direct_dependency=True,
                    is_in_bom=False,
                    version_source="direct",
                    source_location="pom.xml",
                    links=[],
                    fix_available=True,
                )
            )

        for i in range(3):
            vulns_aws.append(
                JavaVulnerability(
                    module="test",
                    group_id="com.amazonaws",
                    artifact_id="aws-sdk",
                    installed_version="1.0.0",
                    vulnerability_id=f"CVE-AWS-{i}",
                    cve_id=f"CVE-AWS-{i}",
                    severity="medium",
                    description=f"AWS vuln {i}",
                    recommendation="1.1.0",
                    in_profile="aws",
                    direct_dependency=True,
                    is_in_bom=False,
                    version_source="direct",
                    source_location="pom.xml",
                    links=[],
                    fix_available=True,
                )
            )

        profile_results = {
            "azure": {
                "vulnerabilities": vulns_azure,
                "total_vulnerabilities": 5,
                "severity_counts": {"high": 5},
            },
            "aws": {
                "vulnerabilities": vulns_aws,
                "total_vulnerabilities": 3,
                "severity_counts": {"medium": 3},
            },
        }

        # Test with pagination (max 5 results, offset 0)
        result = _aggregate_profile_results(profile_results, max_results=5, offset=0)

        assert result["total_vulnerabilities"] == 8  # 5 + 3
        assert len(result["vulnerabilities"]) == 5  # Paginated
        assert result["pagination"].has_more is True
        assert result["pagination"].total_results == 8

    def test_aggregate_profile_results_severity_counts(self):
        """Test that severity counts are correctly aggregated across profiles."""
        from mvn_mcp_server.tools.java_security_scan import _aggregate_profile_results
        from mvn_mcp_server.shared.data_types import JavaVulnerability

        # Azure: 2 critical, 1 high
        azure_vulns = [
            JavaVulnerability(
                module="test",
                group_id="com.azure",
                artifact_id="azure-core",
                installed_version="1.0.0",
                vulnerability_id="CVE-1",
                cve_id="CVE-1",
                severity="critical",
                description="Test",
                recommendation="1.1.0",
                in_profile="azure",
                direct_dependency=True,
                is_in_bom=False,
                version_source="direct",
                source_location="pom.xml",
                links=[],
                fix_available=True,
            ),
            JavaVulnerability(
                module="test",
                group_id="com.azure",
                artifact_id="azure-storage",
                installed_version="1.0.0",
                vulnerability_id="CVE-2",
                cve_id="CVE-2",
                severity="critical",
                description="Test",
                recommendation="1.1.0",
                in_profile="azure",
                direct_dependency=True,
                is_in_bom=False,
                version_source="direct",
                source_location="pom.xml",
                links=[],
                fix_available=True,
            ),
            JavaVulnerability(
                module="test",
                group_id="com.azure",
                artifact_id="azure-identity",
                installed_version="1.0.0",
                vulnerability_id="CVE-3",
                cve_id="CVE-3",
                severity="high",
                description="Test",
                recommendation="1.1.0",
                in_profile="azure",
                direct_dependency=True,
                is_in_bom=False,
                version_source="direct",
                source_location="pom.xml",
                links=[],
                fix_available=True,
            ),
        ]

        # AWS: 1 critical, 2 medium
        aws_vulns = [
            JavaVulnerability(
                module="test",
                group_id="com.amazonaws",
                artifact_id="aws-sdk",
                installed_version="1.0.0",
                vulnerability_id="CVE-4",
                cve_id="CVE-4",
                severity="critical",
                description="Test",
                recommendation="1.1.0",
                in_profile="aws",
                direct_dependency=True,
                is_in_bom=False,
                version_source="direct",
                source_location="pom.xml",
                links=[],
                fix_available=True,
            ),
            JavaVulnerability(
                module="test",
                group_id="com.amazonaws",
                artifact_id="aws-s3",
                installed_version="1.0.0",
                vulnerability_id="CVE-5",
                cve_id="CVE-5",
                severity="medium",
                description="Test",
                recommendation="1.1.0",
                in_profile="aws",
                direct_dependency=True,
                is_in_bom=False,
                version_source="direct",
                source_location="pom.xml",
                links=[],
                fix_available=True,
            ),
            JavaVulnerability(
                module="test",
                group_id="com.amazonaws",
                artifact_id="aws-ec2",
                installed_version="1.0.0",
                vulnerability_id="CVE-6",
                cve_id="CVE-6",
                severity="medium",
                description="Test",
                recommendation="1.1.0",
                in_profile="aws",
                direct_dependency=True,
                is_in_bom=False,
                version_source="direct",
                source_location="pom.xml",
                links=[],
                fix_available=True,
            ),
        ]

        profile_results = {
            "azure": {
                "vulnerabilities": azure_vulns,
                "total_vulnerabilities": 3,
                "severity_counts": {"critical": 2, "high": 1},
            },
            "aws": {
                "vulnerabilities": aws_vulns,
                "total_vulnerabilities": 3,
                "severity_counts": {"critical": 1, "medium": 2},
            },
        }

        result = _aggregate_profile_results(profile_results, max_results=100, offset=0)

        # Verify aggregated severity counts: 3 critical, 1 high, 2 medium
        assert result["severity_counts"]["critical"] == 3
        assert result["severity_counts"]["high"] == 1
        assert result["severity_counts"]["medium"] == 2

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    @patch("mvn_mcp_server.tools.java_security_scan._run_trivy_scan")
    def test_profile_scan_no_vulnerabilities_found(
        self, mock_trivy, mock_maven, mock_check_trivy, tmp_path
    ):
        """Test profile scanning when no vulnerabilities are found."""
        # Setup
        workspace = tmp_path / "test-project"
        workspace.mkdir()
        (workspace / "pom.xml").write_text("<project></project>")

        mock_check_trivy.return_value = True
        mock_maven.check_maven_availability.return_value = True

        # Mock effective POM
        azure_pom = tmp_path / "effective-azure.xml"
        azure_pom.write_text("<project></project>")
        mock_maven.generate_effective_poms_for_profiles.return_value = {
            "azure": azure_pom
        }

        # Mock Trivy - NO vulnerabilities
        mock_trivy.return_value = {"Results": []}

        result = scan_java_project(str(workspace), include_profiles=["azure"])

        assert result["status"] == "success"
        assert result["result"]["scan_mode"] == "profile-effective"
        assert result["result"]["vulnerabilities_found"] is False
        assert result["result"]["total_vulnerabilities"] == 0
        assert (
            result["result"]["per_profile_results"]["azure"]["total_vulnerabilities"]
            == 0
        )

    @patch("mvn_mcp_server.tools.java_security_scan.check_trivy_availability")
    @patch("mvn_mcp_server.tools.java_security_scan.MavenEffectivePomService")
    @patch("mvn_mcp_server.tools.java_security_scan._run_trivy_scan")
    def test_profile_scan_with_pagination_across_profiles(
        self, mock_trivy, mock_maven, mock_check_trivy, tmp_path
    ):
        """Test pagination when aggregating results from multiple profiles."""
        # Setup
        workspace = tmp_path / "test-project"
        workspace.mkdir()
        (workspace / "pom.xml").write_text("<project></project>")

        mock_check_trivy.return_value = True
        mock_maven.check_maven_availability.return_value = True

        # Mock effective POMs
        azure_pom = tmp_path / "effective-azure.xml"
        aws_pom = tmp_path / "effective-aws.xml"
        azure_pom.write_text("<project></project>")
        aws_pom.write_text("<project></project>")

        mock_maven.generate_effective_poms_for_profiles.return_value = {
            "azure": azure_pom,
            "aws": aws_pom,
        }

        # Mock Trivy - 10 vulnerabilities in azure, 10 in aws (20 total)
        def mock_trivy_side_effect(pom_path):
            vulns = []
            profile = "azure" if "azure" in str(pom_path) else "aws"
            for i in range(10):
                vulns.append(
                    {
                        "VulnerabilityID": f"CVE-{profile.upper()}-{i}",
                        "PkgID": f"com.{profile}:lib:1.0.0",
                        "Severity": "MEDIUM",
                        "Description": "Test",
                        "FixedVersion": "1.1.0",
                        "References": [],
                    }
                )
            return {"Results": [{"Target": "pom.xml", "Vulnerabilities": vulns}]}

        mock_trivy.side_effect = mock_trivy_side_effect

        # Execute with pagination (first 15 results)
        result = scan_java_project(
            str(workspace), include_profiles=["azure", "aws"], max_results=15, offset=0
        )

        assert result["status"] == "success"
        assert result["result"]["total_vulnerabilities"] == 20
        assert len(result["result"]["vulnerabilities"]) == 15
        assert result["result"]["pagination"]["has_more"] is True
        assert result["result"]["pagination"]["total_results"] == 20
