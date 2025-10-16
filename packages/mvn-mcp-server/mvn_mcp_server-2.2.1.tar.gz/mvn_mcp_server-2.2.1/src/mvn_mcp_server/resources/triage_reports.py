"""
Triage report resource management for Maven dependency analysis.

Provides structured storage and retrieval of vulnerability triage reports
following enterprise workflow patterns with full data validation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TriageMetadata(BaseModel):
    """Metadata for triage reports following enterprise workflow pattern."""

    report_id: str = Field(..., description="Unique report identifier")
    service_name: str = Field(..., description="Service being analyzed")
    workspace: str = Field(..., description="Workspace path analyzed")
    timestamp: str = Field(..., description="ISO timestamp of analysis")
    version: str = Field(default="1.0", description="Report format version")
    total_dependencies: int = Field(..., description="Total dependencies analyzed")
    vulnerabilities_found: int = Field(..., description="Total vulnerabilities found")
    critical_count: int = Field(default=0, description="Critical vulnerabilities")
    high_count: int = Field(default=0, description="High vulnerabilities")
    medium_count: int = Field(default=0, description="Medium vulnerabilities")
    low_count: int = Field(default=0, description="Low vulnerabilities")


class VulnerabilityFinding(BaseModel):
    """Individual vulnerability finding from triage."""

    cve_id: str = Field(..., description="CVE identifier")
    severity: str = Field(..., description="Vulnerability severity")
    dependency: str = Field(..., description="Affected dependency")
    current_version: str = Field(..., description="Current vulnerable version")
    fix_version: str = Field(
        ..., description="Minimum version that fixes vulnerability"
    )
    cvss_score: Optional[float] = Field(None, description="CVSS score if available")
    description: str = Field(..., description="Vulnerability description")


class DependencyUpdate(BaseModel):
    """Dependency update information from triage."""

    dependency: str = Field(..., description="Maven coordinates")
    current_version: str = Field(..., description="Current version")
    latest_version: str = Field(..., description="Latest available version")
    update_type: str = Field(..., description="MAJOR/MINOR/PATCH")
    module_location: str = Field(..., description="POM file containing dependency")
    age_months: Optional[int] = Field(
        None, description="Age of current version in months"
    )


class TriageReport(BaseModel):
    """Complete triage report structure following enterprise workflow pattern."""

    metadata: TriageMetadata
    vulnerabilities: List[VulnerabilityFinding] = Field(default_factory=list)
    dependency_updates: List[DependencyUpdate] = Field(default_factory=list)
    pom_hierarchy: Dict[str, Any] = Field(default_factory=dict)
    recommendations: Dict[str, List[str]] = Field(default_factory=dict)
    raw_scan_data: Optional[Dict[str, Any]] = Field(
        None, description="Original scan output"
    )


class TriageReportResource:
    """Manages triage report storage and retrieval following enterprise workflow patterns."""

    def __init__(self):
        self._reports: Dict[str, TriageReport] = {}
        self._history: Dict[str, List[TriageReport]] = {}

    async def get_report(self, service_name: str) -> Optional[TriageReport]:
        """Retrieve the latest triage report for a service."""
        return self._reports.get(service_name)

    async def save_report(
        self, service_name: str, report_data: Dict[str, Any]
    ) -> TriageReport:
        """Save a triage report with validation and metadata."""
        # Generate report ID following enterprise pattern
        timestamp = datetime.now().isoformat()
        report_id = f"{service_name}-triage-{timestamp[:10]}"

        # Create metadata
        metadata = TriageMetadata(
            report_id=report_id,
            service_name=service_name,
            workspace=report_data.get("workspace", f"./{service_name}"),
            timestamp=timestamp,
            total_dependencies=len(report_data.get("dependency_updates", [])),
            vulnerabilities_found=len(report_data.get("vulnerabilities", [])),
            critical_count=len(
                [
                    v
                    for v in report_data.get("vulnerabilities", [])
                    if v.get("severity") == "CRITICAL"
                ]
            ),
            high_count=len(
                [
                    v
                    for v in report_data.get("vulnerabilities", [])
                    if v.get("severity") == "HIGH"
                ]
            ),
            medium_count=len(
                [
                    v
                    for v in report_data.get("vulnerabilities", [])
                    if v.get("severity") == "MEDIUM"
                ]
            ),
            low_count=len(
                [
                    v
                    for v in report_data.get("vulnerabilities", [])
                    if v.get("severity") == "LOW"
                ]
            ),
        )

        # Create structured report
        report = TriageReport(
            metadata=metadata,
            vulnerabilities=[
                VulnerabilityFinding(**v)
                for v in report_data.get("vulnerabilities", [])
            ],
            dependency_updates=[
                DependencyUpdate(**d) for d in report_data.get("dependency_updates", [])
            ],
            pom_hierarchy=report_data.get("pom_hierarchy", {}),
            recommendations=report_data.get("recommendations", {}),
            raw_scan_data=report_data.get("raw_scan_data"),
        )

        # Store latest report
        self._reports[service_name] = report

        # Store in history
        if service_name not in self._history:
            self._history[service_name] = []
        self._history[service_name].append(report)

        return report

    async def get_report_summary(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get summary information for plan generation."""
        report = await self.get_report(service_name)
        if not report:
            return None

        return {
            "report_id": report.metadata.report_id,
            "timestamp": report.metadata.timestamp,
            "total_dependencies": report.metadata.total_dependencies,
            "vulnerability_counts": {
                "critical": report.metadata.critical_count,
                "high": report.metadata.high_count,
                "medium": report.metadata.medium_count,
                "low": report.metadata.low_count,
            },
            "critical_vulnerabilities": [
                v for v in report.vulnerabilities if v.severity == "CRITICAL"
            ],
            "high_priority_updates": [
                d
                for d in report.dependency_updates
                if d.update_type == "MAJOR" or (d.age_months and d.age_months > 12)
            ],
        }

    async def get_report_data(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get complete report data as dictionary for resource access."""
        report = await self.get_report(service_name)
        if not report:
            return None

        return report.model_dump()

    def list_services(self) -> List[str]:
        """List all services with triage reports."""
        return list(self._reports.keys())
