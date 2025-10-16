"""
Tests for dependency_triage prompt functionality.

Validates prompt content generation, workflow structure, and enterprise patterns.
"""

import pytest
from mvn_mcp_server.prompts.triage import dependency_triage


class TestDependencyTriage:
    """Test suite for dependency_triage prompt."""

    @pytest.mark.asyncio
    async def test_dependency_triage_basic_parameters(self):
        """Test basic functionality with required parameters."""
        result = await dependency_triage("test-service")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "test-service" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_dependency_triage_with_workspace(self):
        """Test functionality with custom workspace parameter."""
        result = await dependency_triage("test-service", "/custom/workspace")

        content = result[0]["content"]
        assert "/custom/workspace" in content
        assert "test-service" in content

    @pytest.mark.asyncio
    async def test_default_workspace_path(self):
        """Test that default workspace path is correctly generated."""
        result = await dependency_triage("my-service")

        content = result[0]["content"]
        assert "./my-service" in content

    @pytest.mark.asyncio
    async def test_workflow_phases_present(self):
        """Test that all workflow phases are present."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for all phases
        assert "### Phase 1: Project Discovery" in content
        assert "### Phase 2: Version Analysis" in content
        assert "### Phase 3: Security Assessment" in content
        assert "### Phase 4: Triage Report Generation" in content
        assert "### Phase 5: Resource Storage" in content

    @pytest.mark.asyncio
    async def test_phase_objectives_and_tasks(self):
        """Test that each phase has clear objectives and tasks."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for objectives
        assert "**Objective:**" in content

        # Check for numbered tasks
        assert "**Tasks:**" in content
        assert "1. **POM Hierarchy Analysis**" in content
        assert "2. **Dependency Extraction**" in content
        assert "3. **Batch Version Checking**" in content

    @pytest.mark.asyncio
    async def test_tool_integration_instructions(self):
        """Test that tool integration instructions are present."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for specific tool calls
        assert "check_version_batch_tool" in content
        assert "list_available_versions_tool" in content
        assert "scan_java_project_tool" in content

        # Check for tool parameters
        assert "scan_mode:" in content
        assert "severity_filter:" in content
        assert "max_results:" in content

    @pytest.mark.asyncio
    async def test_report_structure_template(self):
        """Test that comprehensive report structure template is included."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for report sections
        assert "## Executive Summary" in content
        assert "## Critical Findings (Action Required)" in content
        assert "## Standard Findings (Planned Updates)" in content
        assert "## Project Structure Analysis" in content
        assert "## Recommended Update Strategy" in content

    @pytest.mark.asyncio
    async def test_vulnerability_table_format(self):
        """Test that vulnerability table format is specified."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for table headers
        assert (
            "| CVE ID | Severity | Dependency | Current | Fix Version | CVSS | Description |"
            in content
        )
        assert (
            "|--------|----------|------------|---------|-------------|------|-------------|"
            in content
        )

    @pytest.mark.asyncio
    async def test_timestamp_inclusion(self):
        """Test that timestamp is included in the prompt."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for timestamp pattern (ISO format)
        assert "**Analysis Date:**" in content
        # The exact timestamp will vary, but should be in ISO format

    @pytest.mark.asyncio
    async def test_resource_storage_instructions(self):
        """Test that resource storage instructions are clear."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for resource storage instructions
        assert "triage://reports/test-service/latest" in content
        assert "Store Triage Report" in content
        assert "Include metadata:" in content

    @pytest.mark.asyncio
    async def test_success_factors_present(self):
        """Test that critical success factors are outlined."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for success factors
        assert "## Critical Success Factors" in content
        assert "**Completeness:**" in content
        assert "**Accuracy:**" in content
        assert "**Actionability:**" in content
        assert "**Traceability:**" in content

    @pytest.mark.asyncio
    async def test_enterprise_workflow_pattern(self):
        """Test that enterprise workflow patterns are followed."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for enterprise elements
        assert "enterprise workflow" in content
        assert "Phase 1: Critical Security (Immediate)" in content
        assert "Phase 2: High Priority Updates (This Sprint)" in content
        assert "Phase 3: Maintenance Updates (Next Sprint)" in content

    @pytest.mark.asyncio
    async def test_implementation_guidelines(self):
        """Test that implementation guidelines are comprehensive."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for implementation guidance
        assert "## Implementation Guidelines" in content
        assert "### Tool Usage Sequence" in content
        assert "### Data Collection Requirements" in content
        assert "### Report Quality Standards" in content

    @pytest.mark.asyncio
    async def test_next_step_guidance(self):
        """Test that next step guidance is provided."""
        result = await dependency_triage("test-service")
        content = result[0]["content"]

        # Check for next steps
        assert "plan" in content
        assert "Next Step:" in content or "next workflow step" in content

    @pytest.mark.asyncio
    async def test_service_name_substitution(self):
        """Test that service name is properly substituted throughout."""
        service_name = "complex-service-name"
        result = await dependency_triage(service_name)
        content = result[0]["content"]

        # Check that service name appears in multiple places
        service_occurrences = content.count(service_name)
        assert service_occurrences >= 3  # Should appear in multiple contexts
