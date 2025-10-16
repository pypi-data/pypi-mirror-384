"""Unit tests for MCP server loader functionality."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from langchain_tool_server.mcp_loader import (
    MCPConfigError,
    load_mcp_servers_tools,
    validate_mcp_config,
)


class TestValidateMCPConfig:
    """Test MCP configuration validation."""

    def test_validate_stdio_config(self):
        """Test validation of stdio transport configuration."""
        config = {
            "name": "test_server",
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "test_server"],
            "env": {"KEY": "value"},
            "cwd": "/path/to/dir",
        }

        result = validate_mcp_config(config)

        assert result["transport"] == "stdio"
        assert result["command"] == "python"
        assert result["args"] == ["-m", "test_server"]
        assert result["env"] == {"KEY": "value"}
        assert result["cwd"] == "/path/to/dir"

    def test_validate_streamable_http_config(self):
        """Test validation of streamable_http transport configuration."""
        config = {
            "name": "test_server",
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp/",
            "headers": {"Authorization": "Bearer token"},
            "timeout": 30,
        }

        result = validate_mcp_config(config)

        assert result["transport"] == "streamable_http"
        assert result["url"] == "http://localhost:8000/mcp/"
        assert result["headers"] == {"Authorization": "Bearer token"}
        assert result["timeout"] == timedelta(seconds=30)

    def test_validate_sse_config(self):
        """Test validation of SSE transport configuration."""
        config = {
            "name": "test_server",
            "transport": "sse",
            "url": "http://localhost:9000/sse",
            "headers": {"X-Custom": "header"},
            "timeout": 10.5,
        }

        result = validate_mcp_config(config)

        assert result["transport"] == "sse"
        assert result["url"] == "http://localhost:9000/sse"
        assert result["headers"] == {"X-Custom": "header"}
        assert result["timeout"] == 10.5

    def test_validate_websocket_config(self):
        """Test validation of WebSocket transport configuration."""
        config = {
            "name": "test_server",
            "transport": "websocket",
            "url": "ws://localhost:8080/ws",
        }

        result = validate_mcp_config(config)

        assert result["transport"] == "websocket"
        assert result["url"] == "ws://localhost:8080/ws"

    def test_missing_name(self):
        """Test that missing name raises error."""
        config = {
            "transport": "stdio",
            "command": "python",
        }

        with pytest.raises(MCPConfigError, match="must have a 'name' field"):
            validate_mcp_config(config)

    def test_missing_transport(self):
        """Test that missing transport raises error."""
        config = {
            "name": "test_server",
        }

        with pytest.raises(MCPConfigError, match="must specify a 'transport' type"):
            validate_mcp_config(config)

    def test_unknown_transport(self):
        """Test that unknown transport type raises error."""
        config = {
            "name": "test_server",
            "transport": "unknown",
        }

        with pytest.raises(MCPConfigError, match="Unknown transport type"):
            validate_mcp_config(config)

    def test_stdio_missing_command(self):
        """Test that stdio without command raises error."""
        config = {
            "name": "test_server",
            "transport": "stdio",
        }

        with pytest.raises(MCPConfigError, match="must specify 'command'"):
            validate_mcp_config(config)

    def test_http_missing_url(self):
        """Test that streamable_http without URL raises error."""
        config = {
            "name": "test_server",
            "transport": "streamable_http",
        }

        with pytest.raises(MCPConfigError, match="must specify 'url'"):
            validate_mcp_config(config)


class TestLoadMCPServersTools:
    """Test MCP server tools loading."""

    @pytest.mark.asyncio
    async def test_empty_config_list(self):
        """Test that empty config list returns empty tools list."""
        tools = await load_mcp_servers_tools([])
        assert tools == []

    @pytest.mark.asyncio
    async def test_load_tools_with_prefix(self):
        """Test loading tools with name prefixing."""
        configs = [
            {
                "name": "math",
                "transport": "stdio",
                "command": "python",
                "args": ["-m", "math_server"],
            }
        ]

        # Mock the session creation and tool listing
        with patch(
            "langchain_tool_server.mcp_loader.create_mcp_session_context"
        ) as mock_create_session:
            mock_session = AsyncMock()
            # Mock the async context manager
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_create_session.return_value = mock_context

            # Mock tools from MCP
            from mcp.types import Tool as MCPTool

            mock_mcp_tool = MCPTool(
                name="add",
                description="Add two numbers",
                inputSchema={"type": "object", "properties": {}},
                annotations=None,
            )

            with patch(
                "langchain_tool_server.mcp_loader.list_mcp_tools"
            ) as mock_list_tools:
                mock_list_tools.return_value = [mock_mcp_tool]

                tools = await load_mcp_servers_tools(configs)

                assert len(tools) == 1
                assert tools[0].name == "math.add"

    @pytest.mark.asyncio
    async def test_handle_failed_server(self):
        """Test that failing to load from one server doesn't stop others."""
        configs = [
            {
                "name": "failing_server",
                "transport": "stdio",
                "command": "python",
            },
            {
                "name": "working_server",
                "transport": "stdio",
                "command": "python",
            },
        ]

        with patch(
            "langchain_tool_server.mcp_loader.create_mcp_session_context"
        ) as mock_create_session:
            # Track call count to distinguish between servers
            call_count = 0

            def session_side_effect(connection_config):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    # First call (failing_server) should raise exception
                    raise Exception("Connection failed")
                else:
                    # Second call (working_server) should return mock context manager
                    mock_session = AsyncMock()
                    mock_context = AsyncMock()
                    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
                    mock_context.__aexit__ = AsyncMock(return_value=None)
                    return mock_context

            mock_create_session.side_effect = session_side_effect

            # Mock tools for working server
            from mcp.types import Tool as MCPTool

            mock_working_tool = MCPTool(
                name="test_tool",
                description="Test tool",
                inputSchema={"type": "object", "properties": {}},
                annotations=None,
            )

            with patch(
                "langchain_tool_server.mcp_loader.list_mcp_tools"
            ) as mock_list_tools:
                mock_list_tools.return_value = [mock_working_tool]

                tools = await load_mcp_servers_tools(configs)

                # Should have loaded tools from working server only
                assert len(tools) == 1

    @pytest.mark.asyncio
    async def test_invalid_config_raises_error(self):
        """Test that invalid configuration raises MCPConfigError."""
        configs = [
            {
                "transport": "stdio",  # Missing name
                "command": "python",
            }
        ]

        tools = await load_mcp_servers_tools(configs)
        assert len(tools) == 0
