"""MCP (Model Context Protocol) server integration for LangChain Tool Server.

This module provides functionality to load tools from MCP servers and convert them
to LangChain tools that can be used within the tool server.
"""

import logging
import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.websocket import websocket_client
from mcp.types import Tool as MCPTool

# Import the Tool class from the tool module
from langchain_tool_server.tool import Tool

logger = logging.getLogger(__name__)


class MCPConfigError(ValueError):
    """Raised when MCP server configuration is invalid."""

    pass


def substitute_env_vars(value: Any) -> Any:
    """Substitute environment variables in configuration values.

    Supports the following patterns:
    - ${{ secrets.VAR_NAME }} -> os.environ['VAR_NAME']
    - ${{ env.VAR_NAME }} -> os.environ['VAR_NAME']
    - ${VAR_NAME} -> os.environ['VAR_NAME']
    - $VAR_NAME -> os.environ['VAR_NAME']

    Args:
        value: Configuration value to process (can be string, dict, list, etc.)

    Returns:
        Value with environment variables substituted

    Raises:
        MCPConfigError: If referenced environment variable is not found
    """
    if isinstance(value, str):
        # Pattern for ${{ secrets.VAR_NAME }} or ${{ env.VAR_NAME }}
        github_pattern = r"\$\{\{\s*(?:secrets|env)\.([A-Z_][A-Z0-9_]*)\s*\}\}"
        # Pattern for ${VAR_NAME}
        brace_pattern = r"\$\{([A-Z_][A-Z0-9_]*)\}"
        # Pattern for $VAR_NAME (word boundary to avoid partial matches)
        simple_pattern = r"\$([A-Z_][A-Z0-9_]*)\b"

        def replace_env_var(match):
            var_name = match.group(1)
            if var_name not in os.environ:
                raise MCPConfigError(
                    f"Environment variable '{var_name}' not found. "
                    f"Please set it in your environment."
                )
            return os.environ[var_name]

        # Apply substitutions in order of specificity
        value = re.sub(github_pattern, replace_env_var, value)
        value = re.sub(brace_pattern, replace_env_var, value)
        value = re.sub(simple_pattern, replace_env_var, value)

        return value

    elif isinstance(value, dict):
        # Recursively process dictionary values
        return {k: substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        # Recursively process list items
        return [substitute_env_vars(item) for item in value]

    else:
        # Return other types as-is
        return value


class MCPToolAdapter(Tool):
    """Adapter that wraps an MCP Tool to match the Tool interface."""

    def __init__(self, mcp_tool: MCPTool, connection_config: dict):
        """Initialize the adapter with an MCP Tool.

        Args:
            mcp_tool: The MCP tool to wrap
            connection_config: Connection configuration for creating sessions
        """
        self.mcp_tool = mcp_tool
        self.connection_config = connection_config

        # Create a wrapper function for the tool
        wrapper_func = self._create_wrapper_func()

        # Initialize the Tool base class attributes directly
        self.func = wrapper_func
        self.name = f"{self.connection_config['name']}.{mcp_tool.name}"
        self.description = mcp_tool.description or ""

        # Get schemas from the MCP Tool
        self.input_schema = self._get_input_schema()
        self.output_schema = self._get_output_schema()

    def _get_input_schema(self) -> dict:
        """Get input schema from the MCP Tool."""
        if self.mcp_tool.inputSchema:
            return self.mcp_tool.inputSchema
        return {"type": "object", "properties": {}}

    def _get_output_schema(self) -> dict:
        """Get output schema from the MCP Tool."""
        # MCP tools typically return text content
        return {"type": "string"}

    def _create_wrapper_func(self):
        """Create a wrapper function that calls the MCP Tool."""

        async def wrapper(**kwargs):
            """Wrapper function that calls the MCP Tool via a fresh session."""
            # Create a new session for each tool call using proper context manager
            async with create_mcp_session_context(self.connection_config) as session:
                # Initialize session and call the tool
                await session.initialize()
                result = await session.call_tool(self.mcp_tool.name, kwargs)

                # Extract text content from the result
                if result.content:
                    text_contents = []
                    for content in result.content:
                        if hasattr(content, "text"):
                            text_contents.append(content.text)

                    if len(text_contents) == 1:
                        return text_contents[0]
                    elif len(text_contents) > 1:
                        return "\n".join(text_contents)
                    else:
                        return ""
                return ""

        # Set the function name and docstring to match the tool
        wrapper.__name__ = self.mcp_tool.name
        wrapper.__doc__ = self.mcp_tool.description

        return wrapper

    async def __call__(self, *args, user_id: str = None, request=None, **kwargs) -> Any:
        """Call the wrapped tool."""
        # MCP tools don't require auth hook, just call the function
        # Note: user_id and request parameters are accepted to match the Tool interface
        # but are not used for MCP tools
        result = await self.func(**kwargs)
        return result


def validate_mcp_config(config: dict) -> dict:
    """Validate and normalize an MCP server configuration.

    Args:
        config: Raw MCP server configuration from toolkit.toml

    Returns:
        Normalized configuration dictionary ready for use with MultiServerMCPClient

    Raises:
        MCPConfigError: If configuration is invalid
    """
    # Apply environment variable substitution to the entire config
    config = substitute_env_vars(config)

    if "name" not in config:
        raise MCPConfigError("MCP server configuration must have a 'name' field")

    if "transport" not in config:
        raise MCPConfigError(
            f"MCP server '{config['name']}' must specify a 'transport' type"
        )

    transport = config["transport"]
    name = config["name"]

    # Create the connection config based on transport type
    connection_config: Dict[str, Any] = {"transport": transport, "name": name}

    if transport == "stdio":
        # stdio transport requires command and optionally args, env, cwd
        if "command" not in config:
            raise MCPConfigError(
                f"MCP server '{name}' with stdio transport must specify 'command'"
            )
        connection_config["command"] = config["command"]

        if "args" in config:
            connection_config["args"] = config["args"]

        if "env" in config:
            connection_config["env"] = config["env"]

        if "cwd" in config:
            connection_config["cwd"] = config["cwd"]

    elif transport == "streamable_http":
        # streamable_http transport requires url and optionally headers, timeout
        if "url" not in config:
            raise MCPConfigError(
                f"MCP server '{name}' with streamable_http transport must specify 'url'"
            )
        connection_config["url"] = config["url"]

        if "headers" in config:
            connection_config["headers"] = config["headers"]

        if "timeout" in config:
            # Convert timeout from seconds to timedelta
            connection_config["timeout"] = timedelta(seconds=config["timeout"])

    elif transport == "sse":
        # SSE transport requires url and optionally headers, timeout
        if "url" not in config:
            raise MCPConfigError(
                f"MCP server '{name}' with sse transport must specify 'url'"
            )
        connection_config["url"] = config["url"]

        if "headers" in config:
            connection_config["headers"] = config["headers"]

        if "timeout" in config:
            # SSE timeout is a float in seconds
            connection_config["timeout"] = float(config["timeout"])

    elif transport == "websocket":
        # WebSocket transport requires url
        if "url" not in config:
            raise MCPConfigError(
                f"MCP server '{name}' with websocket transport must specify 'url'"
            )
        connection_config["url"] = config["url"]

    else:
        raise MCPConfigError(
            f"Unknown transport type '{transport}' for MCP server '{name}'. "
            f"Supported types: stdio, streamable_http, sse, websocket"
        )

    return connection_config


@asynccontextmanager
async def create_mcp_session_context(
    connection_config: dict,
) -> AsyncIterator[ClientSession]:
    """Create an MCP client session from a connection configuration.

    Args:
        connection_config: Validated connection configuration

    Yields:
        ClientSession for communicating with the MCP server

    Raises:
        ValueError: If transport type is not supported
    """
    transport = connection_config["transport"]
    session_kwargs = connection_config.get("session_kwargs", {})

    if transport == "stdio":
        command = connection_config["command"]
        args = connection_config.get("args", [])
        env = connection_config.get("env", {})
        cwd = connection_config.get("cwd")

        # Ensure PATH is set for command execution
        if "PATH" not in env:
            env["PATH"] = os.environ.get("PATH", "")

        # Create stdio server parameters
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
            cwd=cwd,
        )

        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write, **session_kwargs) as session,
        ):
            yield session

    elif transport == "streamable_http":
        url = connection_config["url"]
        headers = connection_config.get("headers")
        timeout = connection_config.get("timeout")  # This should be a timedelta
        sse_read_timeout = connection_config.get("sse_read_timeout")
        terminate_on_close = connection_config.get("terminate_on_close", True)

        async with (
            streamablehttp_client(
                url=url,
                headers=headers,
                timeout=timeout,
                sse_read_timeout=sse_read_timeout,
                terminate_on_close=terminate_on_close,
            ) as (read, write, _),
            ClientSession(read, write, **session_kwargs) as session,
        ):
            yield session

    elif transport == "sse":
        url = connection_config["url"]
        headers = connection_config.get("headers")
        timeout = connection_config.get("timeout", 5.0)  # Default 5 seconds
        sse_read_timeout = connection_config.get(
            "sse_read_timeout", 300.0
        )  # Default 5 minutes

        async with (
            sse_client(
                url=url,
                headers=headers,
                timeout=timeout,
                sse_read_timeout=sse_read_timeout,
            ) as (read, write),
            ClientSession(read, write, **session_kwargs) as session,
        ):
            yield session

    elif transport == "websocket":
        url = connection_config["url"]

        async with (
            websocket_client(url=url) as (read, write),
            ClientSession(read, write, **session_kwargs) as session,
        ):
            yield session

    else:
        raise ValueError(f"Unsupported transport type: {transport}")


async def list_mcp_tools(session: ClientSession) -> List[MCPTool]:
    """List all tools from an MCP session with pagination support.

    Args:
        session: MCP client session

    Returns:
        List of MCP tools

    Raises:
        RuntimeError: If pagination exceeds maximum iterations
    """
    tools = []
    cursor = None
    max_iterations = 1000
    iteration = 0

    while True:
        iteration += 1
        if iteration > max_iterations:
            raise RuntimeError("Exceeded maximum iterations while listing MCP tools")

        # List tools with pagination
        result = await session.list_tools(cursor=cursor)

        if result.tools:
            tools.extend(result.tools)

        # Check if there are more pages
        if not result.nextCursor:
            break

        cursor = result.nextCursor

    return tools


async def load_mcp_servers_tools(
    mcp_configs: List[Dict[str, Any]],
) -> List[Any]:  # Returns list of MCPToolAdapter instances
    """Load tools from multiple MCP servers.

    Args:
        mcp_configs: List of MCP server configurations from toolkit.toml

    Returns:
        List of MCPToolAdapter instances wrapping the MCP tools

    Raises:
        MCPConfigError: If any server configuration is invalid
    """
    if not mcp_configs:
        return []

    all_tools: List[Any] = []  # Will contain MCPToolAdapter instances
    failed_servers: List[str] = []

    # Load tools from each server
    for config in mcp_configs:
        server_name = None
        try:
            server_name = config.get("name")
            if not server_name:
                raise MCPConfigError(
                    "MCP server configuration must have a 'name' field"
                )

            logger.info(f"Loading tools from MCP server: {server_name}")

            # Validate and normalize the configuration
            connection_config = validate_mcp_config(config)

            # Create session and list tools using proper context manager
            async with create_mcp_session_context(connection_config) as session:
                await session.initialize()
                mcp_tools = await list_mcp_tools(session)

                # Wrap each MCP Tool with MCPToolAdapter
                adapted_tools = []
                for mcp_tool in mcp_tools:
                    # Prefix tool name with server name to avoid conflicts
                    prefixed_tool = MCPTool(
                        name=mcp_tool.name,
                        description=mcp_tool.description,
                        inputSchema=mcp_tool.inputSchema,
                        annotations=mcp_tool.annotations,
                    )

                    # Create adapter wrapper
                    adapter = MCPToolAdapter(prefixed_tool, connection_config)
                    adapted_tools.append(adapter)

                all_tools.extend(adapted_tools)
                logger.info(
                    f"Successfully loaded {len(adapted_tools)} tools from MCP server: {server_name}"
                )

        except Exception as e:
            logger.error(
                f"Failed to load tools from MCP server '{server_name or 'unknown'}': {e}"
            )
            if server_name:
                failed_servers.append(server_name)
            # Continue loading from other servers even if one fails

    if failed_servers:
        logger.warning(
            f"Failed to load tools from {len(failed_servers)} MCP server(s): "
            f"{', '.join(failed_servers)}"
        )

    logger.info(f"Total MCP tools loaded: {len(all_tools)}")
    return all_tools
