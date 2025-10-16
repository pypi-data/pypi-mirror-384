"""
Tests for resource management functionality.

Validates triage reports, update plans, and server assets resources
with comprehensive data validation and state management.
"""

import pytest
from unittest.mock import patch
from mvn_mcp_server.resources.triage_reports import (
    TriageReportResource,
    TriageReport,
)
from mvn_mcp_server.resources.update_plans import (
    UpdatePlanResource,
    UpdatePlan,
    TaskStatus,
)
from mvn_mcp_server.resources.server_assets import ServerAssetsResource


class TestTriageReportResource:
    """Test suite for TriageReportResource."""

    @pytest.fixture
    def triage_resource(self):
        """Create a triage resource instance for testing."""
        return TriageReportResource()

    @pytest.fixture
    def sample_report_data(self):
        """Sample triage report data for testing."""
        return {
            "workspace": "./test-service",
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-1234",
                    "severity": "CRITICAL",
                    "dependency": "log4j-core",
                    "current_version": "2.14.1",
                    "fix_version": "2.17.1",
                    "cvss_score": 9.0,
                    "description": "Remote code execution vulnerability",
                }
            ],
            "dependency_updates": [
                {
                    "dependency": "spring-core",
                    "current_version": "5.3.0",
                    "latest_version": "6.1.2",
                    "update_type": "MAJOR",
                    "module_location": "parent-pom.xml",
                    "age_months": 18,
                }
            ],
            "pom_hierarchy": {"parent": "parent-pom.xml"},
            "recommendations": {"critical": ["Update log4j immediately"]},
            "raw_scan_data": {"scan_result": "completed"},
        }

    @pytest.mark.asyncio
    async def test_save_and_retrieve_report(self, triage_resource, sample_report_data):
        """Test saving and retrieving a triage report."""
        service_name = "test-service"

        # Save report
        saved_report = await triage_resource.save_report(
            service_name, sample_report_data
        )

        # Verify report structure
        assert isinstance(saved_report, TriageReport)
        assert saved_report.metadata.service_name == service_name
        assert len(saved_report.vulnerabilities) == 1
        assert len(saved_report.dependency_updates) == 1

        # Retrieve report
        retrieved_report = await triage_resource.get_report(service_name)
        assert retrieved_report is not None
        assert retrieved_report.metadata.service_name == service_name

    @pytest.mark.asyncio
    async def test_report_metadata_generation(
        self, triage_resource, sample_report_data
    ):
        """Test that report metadata is correctly generated."""
        service_name = "test-service"

        with patch("mvn_mcp_server.resources.triage_reports.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = (
                "2024-01-24T10:00:00"
            )

            saved_report = await triage_resource.save_report(
                service_name, sample_report_data
            )

            assert saved_report.metadata.report_id == "test-service-triage-2024-01-24"
            assert saved_report.metadata.total_dependencies == 1
            assert saved_report.metadata.vulnerabilities_found == 1
            assert saved_report.metadata.critical_count == 1
            assert saved_report.metadata.high_count == 0

    @pytest.mark.asyncio
    async def test_get_report_summary(self, triage_resource, sample_report_data):
        """Test getting report summary for plan generation."""
        service_name = "test-service"

        await triage_resource.save_report(service_name, sample_report_data)
        summary = await triage_resource.get_report_summary(service_name)

        assert summary is not None
        assert summary["vulnerability_counts"]["critical"] == 1
        assert len(summary["critical_vulnerabilities"]) == 1
        assert (
            len(summary["high_priority_updates"]) == 1
        )  # MAJOR update with age > 12 months

    @pytest.mark.asyncio
    async def test_nonexistent_report(self, triage_resource):
        """Test handling of nonexistent reports."""
        result = await triage_resource.get_report("nonexistent-service")
        assert result is None

        summary = await triage_resource.get_report_summary("nonexistent-service")
        assert summary is None

    @pytest.mark.asyncio
    async def test_report_history_tracking(self, triage_resource, sample_report_data):
        """Test that report history is tracked."""
        service_name = "test-service"

        # Save first report
        await triage_resource.save_report(service_name, sample_report_data)

        # Modify data and save second report
        sample_report_data["vulnerabilities"].append(
            {
                "cve_id": "CVE-2024-5678",
                "severity": "HIGH",
                "dependency": "jackson-databind",
                "current_version": "2.13.0",
                "fix_version": "2.16.1",
                "description": "Data binding vulnerability",
            }
        )

        await triage_resource.save_report(service_name, sample_report_data)

        # Check that history contains both reports
        assert len(triage_resource._history[service_name]) == 2

        # Check that latest report has 2 vulnerabilities
        latest_report = await triage_resource.get_report(service_name)
        assert len(latest_report.vulnerabilities) == 2


class TestUpdatePlanResource:
    """Test suite for UpdatePlanResource."""

    @pytest.fixture
    def plan_resource(self):
        """Create a plan resource instance for testing."""
        return UpdatePlanResource()

    @pytest.fixture
    def sample_plan_data(self):
        """Sample update plan data for testing."""
        return {
            "priority_filter": ["CRITICAL", "HIGH"],
            "phases": [
                {
                    "phase_id": "phase-1",
                    "phase_name": "Critical Security Updates",
                    "priority": "CRITICAL",
                    "description": "Immediate security fixes",
                    "prerequisites": [],
                    "success_criteria": ["All CVEs resolved"],
                    "tasks": [
                        {
                            "task_id": "task-1",
                            "dependency": "log4j-core",
                            "current_version": "2.14.1",
                            "target_version": "2.17.1",
                            "update_type": "PATCH",
                            "priority": "CRITICAL",
                            "complexity": "LOW",
                            "file_location": "parent-pom.xml",
                            "change_description": "Update log4j version property",
                            "traceability_link": "CVE-2024-1234",
                            "cve_ids": ["CVE-2024-1234"],
                            "testing_requirements": ["Smoke tests"],
                            "acceptance_criteria": ["Security scan passes"],
                            "estimated_effort_hours": 2.0,
                        }
                    ],
                }
            ],
            "all_tasks": [
                {
                    "task_id": "task-1",
                    "dependency": "log4j-core",
                    "current_version": "2.14.1",
                    "target_version": "2.17.1",
                    "update_type": "PATCH",
                    "priority": "CRITICAL",
                    "complexity": "LOW",
                    "file_location": "parent-pom.xml",
                    "change_description": "Update log4j version property",
                    "traceability_link": "CVE-2024-1234",
                    "cve_ids": ["CVE-2024-1234"],
                    "testing_requirements": ["Smoke tests"],
                    "acceptance_criteria": ["Security scan passes"],
                    "estimated_effort_hours": 2.0,
                }
            ],
            "version_control_strategy": {"branch": "feature/security-updates"},
            "testing_strategy": {"required_tests": ["unit", "integration"]},
            "deployment_strategy": {"environment": "staging"},
        }

    @pytest.mark.asyncio
    async def test_save_and_retrieve_plan(self, plan_resource, sample_plan_data):
        """Test saving and retrieving an update plan."""
        service_name = "test-service"
        triage_report_id = "test-service-triage-2024-01-24"

        # Save plan
        saved_plan = await plan_resource.save_plan(
            service_name, sample_plan_data, triage_report_id
        )

        # Verify plan structure
        assert isinstance(saved_plan, UpdatePlan)
        assert saved_plan.metadata.service_name == service_name
        assert saved_plan.metadata.triage_report_id == triage_report_id
        assert len(saved_plan.phases) == 1
        assert len(saved_plan.phases[0].tasks) == 1

        # Retrieve plan
        retrieved_plan = await plan_resource.get_plan(service_name)
        assert retrieved_plan is not None
        assert retrieved_plan.metadata.service_name == service_name

    @pytest.mark.asyncio
    async def test_plan_metadata_generation(self, plan_resource, sample_plan_data):
        """Test that plan metadata is correctly generated."""
        service_name = "test-service"
        triage_report_id = "test-service-triage-2024-01-24"

        with patch("mvn_mcp_server.resources.update_plans.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = (
                "2024-01-24T11:00:00"
            )

            saved_plan = await plan_resource.save_plan(
                service_name, sample_plan_data, triage_report_id
            )

            assert saved_plan.metadata.plan_id == "test-service-plan-2024-01-24"
            assert saved_plan.metadata.total_updates == 1
            assert saved_plan.metadata.total_estimated_hours == 2.0

    @pytest.mark.asyncio
    async def test_progress_calculation(self, plan_resource, sample_plan_data):
        """Test progress calculation functionality."""
        service_name = "test-service"
        triage_report_id = "test-service-triage-2024-01-24"

        saved_plan = await plan_resource.save_plan(
            service_name, sample_plan_data, triage_report_id
        )

        # Check initial progress
        assert saved_plan.progress_summary["total_tasks"] == 1
        assert saved_plan.progress_summary["pending"] == 1
        assert saved_plan.progress_summary["completed"] == 0
        assert saved_plan.progress_summary["completion_percentage"] == 0

    @pytest.mark.asyncio
    async def test_task_status_update(self, plan_resource, sample_plan_data):
        """Test updating task status."""
        service_name = "test-service"
        triage_report_id = "test-service-triage-2024-01-24"

        await plan_resource.save_plan(service_name, sample_plan_data, triage_report_id)

        # Update task status
        success = await plan_resource.update_task_status(
            service_name, "task-1", TaskStatus.COMPLETED
        )
        assert success is True

        # Check updated progress
        updated_plan = await plan_resource.get_plan(service_name)
        assert updated_plan.progress_summary["completed"] == 1
        assert updated_plan.progress_summary["pending"] == 0
        assert updated_plan.progress_summary["completion_percentage"] == 100

    @pytest.mark.asyncio
    async def test_get_plan_summary(self, plan_resource, sample_plan_data):
        """Test getting plan summary."""
        service_name = "test-service"
        triage_report_id = "test-service-triage-2024-01-24"

        await plan_resource.save_plan(service_name, sample_plan_data, triage_report_id)
        summary = await plan_resource.get_plan_summary(service_name)

        assert summary is not None
        assert summary["service_name"] == service_name
        assert summary["triage_report_id"] == triage_report_id
        assert summary["total_updates"] == 1
        assert len(summary["phases"]) == 1


class TestServerAssetsResource:
    """Test suite for ServerAssetsResource."""

    @pytest.fixture
    def assets_resource(self):
        """Create a server assets resource instance for testing."""
        return ServerAssetsResource()

    def test_get_capabilities_structure(self, assets_resource):
        """Test that capabilities structure is comprehensive."""
        capabilities = assets_resource.get_capabilities()

        # Check main structure
        assert "metadata" in capabilities
        assert "prompts" in capabilities
        assert "tools" in capabilities
        assert "resources" in capabilities
        assert "quick_start" in capabilities

    def test_metadata_information(self, assets_resource):
        """Test metadata information."""
        capabilities = assets_resource.get_capabilities()
        metadata = capabilities["metadata"]

        assert metadata["server_name"] == "Maven MCP Server"
        assert metadata["version"] == "1.0.0"
        assert "last_updated" in metadata
        assert "description" in metadata

    def test_prompts_information(self, assets_resource):
        """Test prompts information structure."""
        capabilities = assets_resource.get_capabilities()
        prompts = capabilities["prompts"]

        assert isinstance(prompts, list)
        assert len(prompts) == 3  # list_mcp_assets, dependency_triage, update_plan

        # Check first prompt structure
        prompt = prompts[0]
        assert "name" in prompt
        assert "description" in prompt
        assert "arguments" in prompt
        assert "usage" in prompt

    def test_tools_information(self, assets_resource):
        """Test tools information structure."""
        capabilities = assets_resource.get_capabilities()
        tools = capabilities["tools"]

        assert isinstance(tools, list)
        assert len(tools) == 2  # Version Management and Security Scanning categories

        # Check category structure
        category = tools[0]
        assert "category" in category
        assert "tools" in category

        # Check tool structure
        tool = category["tools"][0]
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool

    def test_resources_information(self, assets_resource):
        """Test resources information structure."""
        capabilities = assets_resource.get_capabilities()
        resources = capabilities["resources"]

        assert isinstance(resources, list)
        assert len(resources) == 3  # triage, plans, assets resources

        # Check resource structure
        resource = resources[0]
        assert "uri_pattern" in resource
        assert "description" in resource
        assert "data_format" in resource
        assert "usage" in resource

    def test_quick_start_information(self, assets_resource):
        """Test quick start information structure."""
        capabilities = assets_resource.get_capabilities()
        quick_start = capabilities["quick_start"]

        assert "workflow_steps" in quick_start
        assert "pro_tips" in quick_start

        # Check workflow steps
        steps = quick_start["workflow_steps"]
        assert isinstance(steps, list)
        assert len(steps) == 4

        # Check step structure
        step = steps[0]
        assert "step" in step
        assert "action" in step
        assert "command" in step
        assert "result" in step

    def test_comprehensive_tool_coverage(self, assets_resource):
        """Test that all expected tools are covered."""
        capabilities = assets_resource.get_capabilities()

        # Extract all tool names
        all_tool_names = []
        for category in capabilities["tools"]:
            for tool in category["tools"]:
                all_tool_names.append(tool["name"])

        # Check for expected tools
        expected_tools = [
            "check_version_tool",
            "check_version_batch_tool",
            "list_available_versions_tool",
            "scan_java_project_tool",
            "analyze_pom_file_tool",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in all_tool_names
