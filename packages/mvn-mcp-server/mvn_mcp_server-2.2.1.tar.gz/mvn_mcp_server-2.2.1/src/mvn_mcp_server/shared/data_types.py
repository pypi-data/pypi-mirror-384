"""Data types for mvn MCP Server.

This module contains Pydantic models for request validation and response formatting.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ErrorCode(str, Enum):
    """Error codes for Maven tools."""

    INVALID_INPUT_FORMAT = "INVALID_INPUT_FORMAT"
    INVALID_TARGET_COMPONENT = "INVALID_TARGET_COMPONENT"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    DEPENDENCY_NOT_FOUND = "DEPENDENCY_NOT_FOUND"
    VERSION_NOT_FOUND = "VERSION_NOT_FOUND"
    VERSION_INVALID = "VERSION_INVALID"
    MAVEN_API_ERROR = "MAVEN_API_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

    # Java Security Scan Error Codes
    DIRECTORY_NOT_FOUND = "DIRECTORY_NOT_FOUND"
    NOT_MAVEN_PROJECT = "NOT_MAVEN_PROJECT"
    MAVEN_ERROR = "MAVEN_ERROR"
    TRIVY_NOT_AVAILABLE = "TRIVY_NOT_AVAILABLE"
    TRIVY_ERROR = "TRIVY_ERROR"
    PROFILE_ERROR = "PROFILE_ERROR"
    MULTI_MODULE_ERROR = "MULTI_MODULE_ERROR"

    # Maven Effective POM Error Codes
    MAVEN_NOT_AVAILABLE = "MAVEN_NOT_AVAILABLE"
    MAVEN_EXECUTION_ERROR = "MAVEN_EXECUTION_ERROR"
    EFFECTIVE_POM_GENERATION_ERROR = "EFFECTIVE_POM_GENERATION_ERROR"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"


class MavenVersionCheckRequest(BaseModel):
    """Request model for checking Maven version existence."""

    dependency: str = Field(description="Maven dependency in groupId:artifactId format")
    version: str = Field(description="Version string to check")
    packaging: str = Field(default="jar", description="Package type (jar, war, etc.)")
    classifier: str | None = Field(default=None, description="Optional classifier")

    @field_validator("dependency")
    @classmethod
    def validate_dependency(cls, v: str) -> str:
        """Validate the dependency format (groupId:artifactId)."""
        if not v or not isinstance(v, str):
            raise ValueError("Dependency cannot be empty")

        # Check for groupId:artifactId format
        if ":" not in v or v.count(":") != 1:
            raise ValueError("Dependency must be in groupId:artifactId format")

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate the version string."""
        if not v or not isinstance(v, str):
            raise ValueError("Version cannot be empty")
        return v


class MavenLatestVersionRequest(BaseModel):
    """Request model for getting latest Maven version."""

    dependency: str = Field(description="Maven dependency in groupId:artifactId format")
    packaging: str = Field(default="jar", description="Package type (jar, war, etc.)")
    classifier: str | None = Field(default=None, description="Optional classifier")

    @field_validator("dependency")
    @classmethod
    def validate_dependency(cls, v: str) -> str:
        """Validate the dependency format (groupId:artifactId)."""
        if not v or not isinstance(v, str):
            raise ValueError("Dependency cannot be empty")

        # Check for groupId:artifactId format
        if ":" not in v or v.count(":") != 1:
            raise ValueError("Dependency must be in groupId:artifactId format")

        return v


class MavenLatestComponentVersionRequest(BaseModel):
    """Request model for finding latest component version."""

    dependency: str = Field(description="Maven dependency in groupId:artifactId format")
    version: str = Field(description="Version string to use as reference")
    target_component: str = Field(
        description="Component to find the latest version for ('major', 'minor', or 'patch')"
    )
    packaging: str = Field(default="jar", description="Package type (jar, war, etc.)")
    classifier: str | None = Field(default=None, description="Optional classifier")

    @field_validator("dependency")
    @classmethod
    def validate_dependency(cls, v: str) -> str:
        """Validate the dependency format (groupId:artifactId)."""
        if not v or not isinstance(v, str):
            raise ValueError("Dependency cannot be empty")

        # Check for groupId:artifactId format
        if ":" not in v or v.count(":") != 1:
            raise ValueError("Dependency must be in groupId:artifactId format")

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate the version string."""
        if not v or not isinstance(v, str):
            raise ValueError("Version cannot be empty")
        return v

    @field_validator("target_component")
    @classmethod
    def validate_target_component(cls, v: str) -> str:
        """Validate the target component."""
        if v not in ["major", "minor", "patch"]:
            raise ValueError(
                "Target component must be one of 'major', 'minor', or 'patch'"
            )
        return v


class MavenEnhancedVersionCheckRequest(BaseModel):
    """Request model for enhanced version checking with all version updates."""

    dependency: str = Field(description="Maven dependency in groupId:artifactId format")
    version: str = Field(description="Version string to check and use as reference")
    packaging: str = Field(default="jar", description="Package type (jar, war, etc.)")
    classifier: str | None = Field(default=None, description="Optional classifier")

    @field_validator("dependency")
    @classmethod
    def validate_dependency(cls, v: str) -> str:
        """Validate the dependency format (groupId:artifactId)."""
        if not v or not isinstance(v, str):
            raise ValueError("Dependency cannot be empty")

        # Check for groupId:artifactId format
        if ":" not in v or v.count(":") != 1:
            raise ValueError("Dependency must be in groupId:artifactId format")

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate the version string."""
        if not v or not isinstance(v, str):
            raise ValueError("Version cannot be empty")
        return v


class MavenDependencyItem(BaseModel):
    """Model for a single Maven dependency item in a batch request."""

    dependency: str = Field(description="Maven dependency in groupId:artifactId format")
    version: str = Field(description="Version string to check and use as reference")
    packaging: str = Field(default="jar", description="Package type (jar, war, etc.)")
    classifier: str | None = Field(default=None, description="Optional classifier")

    @field_validator("dependency")
    @classmethod
    def validate_dependency(cls, v: str) -> str:
        """Validate the dependency format (groupId:artifactId)."""
        if not v or not isinstance(v, str):
            raise ValueError("Dependency cannot be empty")

        # Check for groupId:artifactId format
        if ":" not in v or v.count(":") != 1:
            raise ValueError("Dependency must be in groupId:artifactId format")

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate the version string."""
        if not v or not isinstance(v, str):
            raise ValueError("Version cannot be empty")
        return v


class MavenBatchVersionCheckRequest(BaseModel):
    """Request model for batch version checking with all version updates."""

    dependencies: List[MavenDependencyItem] = Field(
        description="List of Maven dependencies to check"
    )

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(
        cls, v: List[MavenDependencyItem]
    ) -> List[MavenDependencyItem]:
        """Validate the dependencies list."""
        if not v or len(v) == 0:
            raise ValueError("At least one dependency is required")
        return v


class MavenListAvailableVersionsRequest(BaseModel):
    """Request model for listing available Maven versions by minor tracks."""

    dependency: str = Field(description="Maven dependency in groupId:artifactId format")
    version: str = Field(description="Current version string to use as reference")
    packaging: str = Field(default="jar", description="Package type (jar, war, etc.)")
    classifier: str | None = Field(default=None, description="Optional classifier")
    include_all_versions: bool = Field(
        default=False, description="Whether to include all versions in the response"
    )

    @field_validator("dependency")
    @classmethod
    def validate_dependency(cls, v: str) -> str:
        """Validate the dependency format (groupId:artifactId)."""
        if not v or not isinstance(v, str):
            raise ValueError("Dependency cannot be empty")

        # Check for groupId:artifactId format
        if ":" not in v or v.count(":") != 1:
            raise ValueError("Dependency must be in groupId:artifactId format")

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate the version string."""
        if not v or not isinstance(v, str):
            raise ValueError("Version cannot be empty")
        return v


class JavaSecurityScanRequest(BaseModel):
    """Request model for scanning Java projects for security vulnerabilities."""

    workspace: str = Field(
        description="The absolute path to the Java project directory"
    )
    include_profiles: Optional[List[str]] = Field(
        default=None, description="Maven profiles to activate during scanning"
    )
    scan_all_modules: bool = Field(
        default=True,
        description="Whether to scan all modules or just the specified project",
    )
    scan_mode: str = Field(
        default="workspace", description="Scan mode (workspace or pom_only)"
    )
    pom_file: Optional[str] = Field(
        default=None,
        description="Path to specific pom.xml file to scan (only used in pom_only mode)",
    )
    severity_filter: Optional[List[str]] = Field(
        default=None,
        description="List of severity levels to include (critical, high, medium, low)",
    )
    max_results: int = Field(
        default=100, description="Maximum number of vulnerability results to return"
    )
    offset: int = Field(default=0, description="Starting offset for paginated results")

    @field_validator("workspace")
    @classmethod
    def validate_workspace(cls, v: str) -> str:
        """Validate the workspace path."""
        if not v or not isinstance(v, str):
            raise ValueError("Workspace path cannot be empty")
        return v

    @field_validator("scan_mode")
    @classmethod
    def validate_scan_mode(cls, v: str) -> str:
        """Validate the scan mode."""
        valid_modes = ["workspace", "pom_only"]
        if v not in valid_modes:
            raise ValueError(f"Invalid scan mode: {v}. Must be one of {valid_modes}")
        return v

    @field_validator("severity_filter")
    @classmethod
    def validate_severity_filter(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate the severity filter."""
        if v is None:
            return v

        valid_severities = ["critical", "high", "medium", "low", "unknown"]
        for severity in v:
            if severity.lower() not in valid_severities:
                raise ValueError(
                    f"Invalid severity: {severity}. Must be one of {valid_severities}"
                )
        return v


class JavaVulnerability(BaseModel):
    """Model for a single Java vulnerability found during scanning."""

    module: str = Field(description="Module name/path where vulnerability was found")
    group_id: str = Field(description="Maven group ID of the vulnerable dependency")
    artifact_id: str = Field(
        description="Maven artifact ID of the vulnerable dependency"
    )
    installed_version: str = Field(
        description="Installed version of the vulnerable dependency"
    )
    vulnerability_id: str = Field(description="Vulnerability identifier")
    cve_id: str = Field(description="CVE identifier")
    severity: str = Field(
        description="Severity level (critical, high, medium, low, unknown)"
    )
    description: str = Field(description="Description of the vulnerability")
    recommendation: str = Field(description="Recommended version to upgrade to")
    in_profile: Optional[str] = Field(
        default=None, description="Profile where the vulnerability was found"
    )
    direct_dependency: bool = Field(
        description="Whether this is a direct dependency or transitive"
    )
    is_in_bom: bool = Field(
        description="Whether this dependency is in a Bill of Materials"
    )
    version_source: str = Field(description="Source of the version definition")
    source_location: str = Field(
        description="File and location where the version is defined"
    )
    links: List[str] = Field(description="Links to vulnerability information")
    fix_available: bool = Field(description="Whether a fixed version exists")


class JavaPaginationInfo(BaseModel):
    """Model for pagination information."""

    offset: int = Field(description="Starting offset for paginated results")
    max_results: int = Field(description="Maximum number of results per page")
    total_results: int = Field(description="Total number of results available")
    has_more: bool = Field(description="Whether more results are available")


class ProfileScanResult(BaseModel):
    """Results for scanning a single Maven profile."""

    profile_id: str = Field(description="Profile identifier")
    effective_pom_used: bool = Field(
        description="Whether effective POM was generated for this profile"
    )
    vulnerabilities_found: bool = Field(
        description="Whether vulnerabilities were found in this profile"
    )
    total_vulnerabilities: int = Field(
        description="Total number of vulnerabilities found in this profile"
    )
    severity_counts: dict = Field(
        description="Counts of vulnerabilities by severity level for this profile"
    )
    vulnerabilities: List[JavaVulnerability] = Field(
        description="List of vulnerabilities found in this profile"
    )


class ProfileSpecificAnalysis(BaseModel):
    """Cross-profile vulnerability analysis."""

    common_to_all_profiles: List[str] = Field(
        description="CVE IDs present in all scanned profiles", default_factory=list
    )
    profile_specific_cves: dict = Field(
        description="CVE IDs unique to each profile (key: profile_id, value: list of CVE IDs)",
        default_factory=dict,
    )


class JavaSecurityScanResult(BaseModel):
    """Model for the result of a Java security scan."""

    scan_mode: str = Field(
        description="Scan mode used (trivy, trivy-pom-only, profile-effective, or basic)"
    )
    vulnerabilities_found: bool = Field(
        description="Whether vulnerabilities were found"
    )
    total_vulnerabilities: int = Field(
        description="Total number of vulnerabilities found"
    )
    modules_scanned: List[str] = Field(description="List of modules scanned")
    profiles_activated: List[str] = Field(
        description="List of profiles activated during scan"
    )
    severity_counts: dict = Field(
        description="Counts of vulnerabilities by severity level"
    )
    vulnerabilities: List[JavaVulnerability] = Field(
        description="List of vulnerabilities found"
    )
    pagination: Optional[JavaPaginationInfo] = Field(
        default=None, description="Pagination information"
    )
    scan_limitations: Optional[List[str]] = Field(
        default=None, description="Limitations of the scan"
    )
    recommendations: Optional[List[str]] = Field(
        default=None, description="Recommendations for improving scan results"
    )
    # Profile-based scanning fields
    per_profile_results: Optional[dict] = Field(
        default=None,
        description="Results broken down by profile (key: profile_id, value: ProfileScanResult dict)",
    )
    profile_specific_vulnerabilities: Optional[ProfileSpecificAnalysis] = Field(
        default=None,
        description="Cross-profile vulnerability analysis showing common vs. profile-specific CVEs",
    )
    maven_available: bool = Field(
        default=False,
        description="Whether Maven was available for profile-based scanning",
    )
