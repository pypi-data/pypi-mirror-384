"""
Tests for update_plan prompt functionality.

Validates prompt content generation, plan structure, and traceability requirements.
"""

import pytest
from mvn_mcp_server.prompts.plan import update_plan


class TestUpdatePlan:
    """Test suite for update_plan prompt."""

    @pytest.mark.asyncio
    async def test_update_plan_basic_parameters(self):
        """Test basic functionality with required parameters."""
        result = await update_plan("test-service")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "test-service" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_update_plan_with_priorities(self):
        """Test functionality with custom priority parameters."""
        result = await update_plan("test-service", ["CRITICAL", "HIGH", "MEDIUM"])

        content = result[0]["content"]
        assert "CRITICAL" in content
        assert "HIGH" in content
        assert "MEDIUM" in content

    @pytest.mark.asyncio
    async def test_default_priorities(self):
        """Test that default priorities are correctly set."""
        result = await update_plan("test-service")

        content = result[0]["content"]
        # Should mention default priorities
        assert "CRITICAL" in content
        assert "HIGH" in content

    @pytest.mark.asyncio
    async def test_triage_report_retrieval_instructions(self):
        """Test that triage report retrieval instructions are clear."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for resource access instructions
        assert "triage://reports/test-service/latest" in content
        assert "### 1. Retrieve and Analyze Triage Report" in content
        assert "<triage_breakdown>" in content

    @pytest.mark.asyncio
    async def test_plan_structure_template(self):
        """Test that plan structure template is comprehensive."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for plan sections
        assert "## Overview" in content
        assert "## References" in content
        assert "## Phases and Tasks" in content
        assert "## Success Criteria" in content
        assert "## Dependency Updates Summary" in content

    @pytest.mark.asyncio
    async def test_phase_structure(self):
        """Test that phase structure follows enterprise pattern."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for specific phases
        assert "### Phase 1: Update Critical Dependencies" in content
        assert "### Phase 2: Update High Priority Dependencies" in content
        assert "### Phase 3: Update Medium/Low Priority Dependencies" in content
        assert "### Phase 4: Security Hardening & Verification" in content
        assert "### Phase 5: Build & Test Verification" in content

    @pytest.mark.asyncio
    async def test_traceability_requirements(self):
        """Test that traceability requirements are emphasized."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for traceability elements
        assert "traceability" in content.lower()
        assert "_Ref: [CVE-ID]" in content
        assert "Triage Table" in content
        assert "### 3. Implementation Guidelines" in content
        assert "**Traceability:**" in content

    @pytest.mark.asyncio
    async def test_tool_integration_commands(self):
        """Test that tool integration commands are specified."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for tool commands
        assert "check_version_tool" in content
        assert "scan_java_project_tool" in content
        assert 'scan_mode="workspace"' in content

    @pytest.mark.asyncio
    async def test_version_control_conventions(self):
        """Test that version control conventions are specified."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for version control guidance
        assert "## Version Control Conventions" in content
        assert "**Branch naming:**" in content
        assert "**Commit message format:**" in content
        assert "**Required PR checks:**" in content

    @pytest.mark.asyncio
    async def test_task_format_requirements(self):
        """Test that task format requirements are detailed."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for task format elements
        assert "- [ ] **Update" in content
        assert "[dependency]" in content
        assert "[current]" in content
        assert "[target]" in content
        assert "[CVE-ID]" in content

    @pytest.mark.asyncio
    async def test_maven_specific_guidance(self):
        """Test that Maven-specific guidance is provided."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for Maven elements
        assert "mvn clean install" in content
        assert "mvn test" in content
        assert "mvn verify" in content
        assert "pom.xml" in content

    @pytest.mark.asyncio
    async def test_quality_assurance_checklist(self):
        """Test that quality assurance checklist is included."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for QA elements
        assert "### 7. Quality Assurance Checklist" in content
        assert "- [ ] Every task references specific triage findings" in content
        assert "- [ ] All CVE IDs from triage are addressed" in content

    @pytest.mark.asyncio
    async def test_resource_storage_instructions(self):
        """Test that resource storage instructions are present."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for storage instructions
        assert "plans://updates/test-service/latest" in content
        assert "### 8. Final Steps" in content
        assert "Store the plan at:" in content

    @pytest.mark.asyncio
    async def test_priority_focus_display(self):
        """Test that priority focus is properly displayed."""
        priorities = ["CRITICAL", "MEDIUM"]
        result = await update_plan("test-service", priorities)
        content = result[0]["content"]

        # Check that priorities are mentioned in focus
        assert "**Priority Focus:** CRITICAL, MEDIUM" in content

    @pytest.mark.asyncio
    async def test_enterprise_structure_emphasis(self):
        """Test that enterprise structure is emphasized."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for enterprise elements
        assert "enterprise workflow" in content
        assert "enterprise structure" in content
        assert "proven enterprise structure" in content

    @pytest.mark.asyncio
    async def test_success_criteria_standards(self):
        """Test that success criteria standards are defined."""
        result = await update_plan("test-service")
        content = result[0]["content"]

        # Check for success criteria elements
        assert "#### Success Criteria Standards" in content
        assert "All security vulnerabilities resolved" in content
        assert "No regression in functionality" in content

    @pytest.mark.asyncio
    async def test_service_name_substitution(self):
        """Test that service name is properly substituted throughout."""
        service_name = "complex-service-name"
        result = await update_plan(service_name)
        content = result[0]["content"]

        # Check that service name appears in multiple contexts
        service_occurrences = content.count(service_name)
        assert service_occurrences >= 5  # Should appear in multiple places
