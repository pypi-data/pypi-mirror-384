"""Integration tests for the MCP server using FastMCP in-memory testing.

These tests validate the actual MCP protocol interactions with our server,
ensuring proper registration and behavior of tools, prompts, and resources.
"""

import pytest
from fastmcp import Client
from mcp.types import TextContent
from mvn_mcp_server.server import mcp


class TestMCPServerIntegration:
    """Test MCP server integration using in-memory client connections."""

    @pytest.fixture
    def client(self):
        """Create a FastMCP client connected to our server."""
        return Client(mcp)

    async def test_server_ping(self, client):
        """Test that the server responds to ping."""
        async with client:
            # Ping may return None in some FastMCP versions, just test it doesn't error
            await client.ping()
            # If we get here without exception, server is responsive
            assert True

    async def test_list_tools(self, client):
        """Test that all expected tools are registered."""
        async with client:
            tools = await client.list_tools()

            tool_names = [tool.name for tool in tools]
            expected_tools = [
                "check_version_tool",
                "check_version_batch_tool",
                "list_available_versions_tool",
                "scan_java_project_tool",
                "analyze_pom_file_tool",
            ]

            for expected_tool in expected_tools:
                assert (
                    expected_tool in tool_names
                ), f"Tool {expected_tool} not found in {tool_names}"

    async def test_list_prompts(self, client):
        """Test that all expected prompts are registered."""
        async with client:
            prompts = await client.list_prompts()

            prompt_names = [prompt.name for prompt in prompts]
            expected_prompts = ["list_mcp_assets_prompt", "triage", "plan"]

            for expected_prompt in expected_prompts:
                assert (
                    expected_prompt in prompt_names
                ), f"Prompt {expected_prompt} not found in {prompt_names}"

    async def test_list_resources(self, client):
        """Test that all expected resources are registered."""
        async with client:
            resources = await client.list_resources()

            # Should have at least the static assets resource
            assert len(resources) >= 1

            # Check for the assets resource which is always available
            resource_uris = [str(resource.uri) for resource in resources]
            assert "assets://server/capabilities" in resource_uris

    async def test_check_version_tool_call(self, client):
        """Test calling the check_version_tool with valid input."""
        async with client:
            result = await client.call_tool(
                "check_version_tool",
                {"dependency": "org.springframework:spring-core", "version": "5.3.0"},
            )

            # Handle both list and CallToolResult formats
            if hasattr(result, "content"):
                # CallToolResult object
                content = result.content
            else:
                # List of content
                content = result

            # Should return content
            assert len(content) > 0
            assert isinstance(content[0], TextContent)

            # Parse the JSON response
            import json

            response_data = json.loads(content[0].text)

            # Check response structure
            assert "tool_name" in response_data
            assert "status" in response_data
            assert response_data["tool_name"] == "check_version"

    async def test_list_mcp_assets_prompt(self, client):
        """Test calling the list_mcp_assets prompt."""
        async with client:
            result = await client.get_prompt("list_mcp_assets_prompt", {})

            # Handle both list and GetPromptResult formats
            if isinstance(result, list):
                messages = result
            else:
                # GetPromptResult object
                assert hasattr(result, "messages")
                messages = result.messages

            assert len(messages) > 0

            # First message should contain our assets information
            message = messages[0]
            assert hasattr(message, "content")
            assert isinstance(message.content, TextContent)
            assert "Maven MCP Server Assets" in message.content.text
            assert "Prompts" in message.content.text
            assert "Tools" in message.content.text
            assert "Resources" in message.content.text

    async def test_triage_prompt_structure(self, client):
        """Test calling the triage prompt with parameters."""
        async with client:
            result = await client.get_prompt("triage", {"service_name": "test-service"})

            # Handle both list and GetPromptResult formats
            if isinstance(result, list):
                messages = result
            else:
                # GetPromptResult object
                assert hasattr(result, "messages")
                messages = result.messages

            assert len(messages) > 0

            message = messages[0]
            assert hasattr(message, "content")
            assert isinstance(message.content, TextContent)
            assert "test-service" in message.content.text
            assert "Dependency Triage" in message.content.text

    async def test_plan_prompt_structure(self, client):
        """Test calling the plan prompt with parameters."""
        async with client:
            result = await client.get_prompt(
                "plan",
                {
                    "service_name": "test-service"
                    # Skip priorities for now since MCP expects strings
                },
            )

            # Handle both list and GetPromptResult formats
            if isinstance(result, list):
                messages = result
            else:
                # GetPromptResult object
                assert hasattr(result, "messages")
                messages = result.messages

            assert len(messages) > 0

            message = messages[0]
            assert hasattr(message, "content")
            assert isinstance(message.content, TextContent)
            assert "test-service" in message.content.text
            assert "Remediation Plan" in message.content.text

    async def test_server_assets_resource(self, client):
        """Test reading the server assets resource."""
        async with client:
            content = await client.read_resource("assets://server/capabilities")

            # Should return structured capability information
            assert len(content) > 0

            # The response should contain capability information
            # (it may be JSON or formatted text)
            response_text = content[0].text
            assert len(response_text) > 0

            # Try to parse as JSON, but don't require it
            try:
                import json

                capabilities = json.loads(response_text)
                assert "prompts" in capabilities
                assert "tools" in capabilities
                assert "resources" in capabilities
            except json.JSONDecodeError:
                # If not JSON, just ensure it contains expected content
                assert "prompts" in response_text.lower()
                assert "tools" in response_text.lower()
                assert "resources" in response_text.lower()

    async def test_tool_error_handling(self, client):
        """Test that tools handle invalid input gracefully."""
        from fastmcp.exceptions import ClientError, ToolError

        async with client:
            # Should raise either ClientError or ToolError for invalid input
            with pytest.raises((ClientError, ToolError)) as exc_info:
                await client.call_tool(
                    "check_version_tool",
                    {
                        "dependency": "invalid-format",  # Missing colon
                        "version": "1.0.0",
                    },
                )

            # Error message should contain relevant information
            error_message = str(exc_info.value)
            assert "groupId:artifactId" in error_message

    async def test_batch_tool_functionality(self, client):
        """Test the batch version checking tool."""
        async with client:
            result = await client.call_tool(
                "check_version_batch_tool",
                {
                    "dependencies": [
                        {
                            "dependency": "org.springframework:spring-core",
                            "version": "5.3.0",
                        },
                        {"dependency": "junit:junit", "version": "4.13.2"},
                    ]
                },
            )

            # Handle both list and CallToolResult formats
            if hasattr(result, "content"):
                # CallToolResult object
                content = result.content
            else:
                # List of content
                content = result

            # Should return batch results
            assert len(content) > 0
            assert isinstance(content[0], TextContent)

            import json

            response_data = json.loads(content[0].text)

            assert response_data["status"] == "success"
            assert "result" in response_data
            assert "summary" in response_data["result"]
            assert "dependencies" in response_data["result"]
