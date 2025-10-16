"""
Tests for list_mcp_assets prompt functionality.

Validates prompt content generation, structure, and dynamic capability listing.
"""

import pytest
from mvn_mcp_server.prompts.list_mcp_assets import list_mcp_assets


class TestListMcpAssets:
    """Test suite for list_mcp_assets prompt."""

    @pytest.mark.asyncio
    async def test_list_mcp_assets_returns_message_list(self):
        """Test that list_mcp_assets returns a list of messages."""
        result = await list_mcp_assets()

        assert isinstance(result, list)
        assert len(result) == 1
        assert "role" in result[0]
        assert "content" in result[0]
        assert result[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_content_includes_all_sections(self):
        """Test that the content includes all required sections."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for main sections
        assert "# 🚀 Maven MCP Server Assets" in content
        assert "## 📝 Prompts" in content
        assert "## 🔧 Tools" in content
        assert "## 📂 Resources" in content
        assert "## 🎯 Quick Start Workflow" in content
        assert "## 💡 Pro Tips" in content

    @pytest.mark.asyncio
    async def test_prompts_section_content(self):
        """Test that prompts section includes all expected prompts."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for specific prompts
        assert "list_mcp_assets" in content
        assert "triage" in content
        assert "plan" in content

        # Check for argument descriptions
        assert "(service_name, workspace)" in content
        assert "(service_name, priorities)" in content

    @pytest.mark.asyncio
    async def test_tools_section_content(self):
        """Test that tools section includes all expected tools."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for tool categories
        assert "### Version Management" in content
        assert "### Security Scanning" in content

        # Check for specific tools
        assert "check_version_tool" in content
        assert "check_version_batch_tool" in content
        assert "list_available_versions_tool" in content
        assert "scan_java_project_tool" in content
        assert "analyze_pom_file_tool" in content

    @pytest.mark.asyncio
    async def test_resources_section_content(self):
        """Test that resources section includes all expected resources."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for resource URIs
        assert "triage://reports/{service_name}/latest" in content
        assert "plans://updates/{service_name}/latest" in content
        assert "assets://server/capabilities" in content

    @pytest.mark.asyncio
    async def test_workflow_example_present(self):
        """Test that workflow example is included."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for workflow steps
        assert "triage" in content
        assert "plan" in content
        assert "scan_java_project_tool" in content

        # Check for enterprise workflow pattern
        assert "Enterprise Dependency Management Pattern" in content

    @pytest.mark.asyncio
    async def test_pro_tips_section(self):
        """Test that pro tips section provides useful guidance."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for key tips
        assert "Triage First" in content
        assert "Resource Persistence" in content
        assert "Batch Processing" in content
        assert "Full Audit Trail" in content

    @pytest.mark.asyncio
    async def test_data_format_examples(self):
        """Test that data format examples are included."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for JSON examples
        assert "## 📊 Resource Data Formats" in content
        assert "### Triage Reports" in content
        assert "### Update Plans" in content
        assert '"cve_id": "CVE-2024-1234"' in content
        assert '"traceability_link"' in content

    @pytest.mark.asyncio
    async def test_content_is_markdown_formatted(self):
        """Test that content is properly formatted as markdown."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        # Check for markdown elements
        assert content.startswith("# ")  # Main heading
        assert "## " in content  # Section headings
        assert "### " in content  # Subsection headings
        assert "• " in content  # Bullet points
        assert "```" in content  # Code blocks

    @pytest.mark.asyncio
    async def test_call_to_action_present(self):
        """Test that call to action is present at the end."""
        result = await list_mcp_assets()
        content = result[0]["content"]

        assert "Ready to get started" in content
        assert "triage" in content.split("Ready to get started")[1]
