"""Test REST API functionality."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from langchain_tool_server import Server


async def test_basic_toolkit_lists_correct_tools_and_tool_invocation_works():
    """Test REST API list tools and tool execution endpoints."""
    # Get path to basic test toolkit (now has both regular and auth tools)
    test_dir = Path(__file__).parent.parent / "toolkits" / "basic"

    # Create server from toolkit (without MCP)
    server = Server.from_toolkit(str(test_dir))

    # Create test client
    transport = ASGITransport(app=server, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # Test REST API list tools endpoint
        response = await client.get("/tools")

        assert response.status_code == 200
        tools = response.json()

        # Verify tools are listed
        assert len(tools) == 4

        # Check tools without auth or interrupts
        hello_tool = next(t for t in tools if t["name"] == "hello")
        assert hello_tool["description"] == "Say hello."
        # Should not have auth fields
        assert "auth_provider" not in hello_tool
        assert "scopes" not in hello_tool
        # Should not have default_interrupt or should be False
        assert hello_tool.get("default_interrupt", False) is False

        add_tool = next(t for t in tools if t["name"] == "add")
        assert add_tool["description"] == "Add two numbers."
        # Should not have auth fields
        assert "auth_provider" not in add_tool
        assert "scopes" not in add_tool
        # Should not have default_interrupt or should be False
        assert add_tool.get("default_interrupt", False) is False

        # Check tool with auth - verify auth info is included
        auth_tool = next(t for t in tools if t["name"] == "test_auth_tool")
        assert auth_tool["description"].startswith(
            "A test tool that requires authentication."
        )
        # Should have auth fields
        assert "auth_provider" in auth_tool
        assert "scopes" in auth_tool
        assert auth_tool["auth_provider"] == "test_provider"
        assert auth_tool["scopes"] == ["test_scope"]
        # Should not have default_interrupt or should be False
        assert auth_tool.get("default_interrupt", False) is False

        # Check tool with default_interrupt=True
        interrupt_tool = next(t for t in tools if t["name"] == "sensitive_action")
        assert interrupt_tool["description"].startswith(
            "A test tool that should have interrupts enabled by default."
        )
        # Should not have auth fields
        assert "auth_provider" not in interrupt_tool
        assert "scopes" not in interrupt_tool
        # Should have default_interrupt=True
        assert "default_interrupt" in interrupt_tool
        assert interrupt_tool["default_interrupt"] is True

        # Test executing a non-auth tool
        response = await client.post(
            "/tools/call",
            json={"request": {"tool_id": "add", "input": {"x": 5, "y": 3}}},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "execution_id" in data
        assert data["value"] == 8


async def test_basic_toolkit_invalid_tool_call_args_returns_400():
    """Test REST API tool call with invalid parameters returns 400."""
    # Get path to test toolkit
    test_dir = Path(__file__).parent.parent / "toolkits" / "basic"

    # Create server from toolkit (without MCP)
    server = Server.from_toolkit(str(test_dir))

    # Create test client
    transport = ASGITransport(app=server, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # Test executing the add tool with wrong parameter names
        response = await client.post(
            "/tools/call",
            json={"request": {"tool_id": "add", "input": {"wrong": 5, "params": 3}}},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        data = response.json()

        # Should return error details
        assert "detail" in data
        assert "Invalid input" in data["detail"]


async def test_basic_toolkit_invalid_mcp_tool_call_args_returns_400():
    """Test MCP tool call with invalid parameters returns proper error."""
    # Get path to test toolkit
    test_dir = Path(__file__).parent.parent / "toolkits" / "basic"

    # Create server from toolkit
    server = Server.from_toolkit(str(test_dir))

    # Create test client
    transport = ASGITransport(app=server, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # Test executing the add tool with wrong parameter names
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "add", "arguments": {"wrong": 5, "params": 3}},
            },
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # MCP should return error in result
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "error" in data
        assert "Invalid input" in data["error"]["message"]


async def test_basic_toolkit_lists_correct_mcp_tools_and_mcp_tool_invocation_works():
    """Test MCP list tools endpoint and MCP tool invocation."""
    # Get path to basic test toolkit (now has both regular and auth tools)
    test_dir = Path(__file__).parent.parent / "toolkits" / "basic"

    # Create server from toolkit
    server = Server.from_toolkit(str(test_dir))

    # Create test client
    transport = ASGITransport(app=server, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # Test MCP list tools endpoint
        response = await client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data

        # Verify tools are listed
        tools = data["result"]["tools"]
        assert len(tools) == 4

        # Check tools without auth or interrupts
        hello_tool = next(t for t in tools if t["name"] == "hello")
        assert hello_tool["description"] == "Say hello."
        # Should not have auth fields
        assert "auth_provider" not in hello_tool
        assert "scopes" not in hello_tool
        # Should not have default_interrupt or should be False
        assert hello_tool.get("default_interrupt", False) is False

        add_tool = next(t for t in tools if t["name"] == "add")
        assert add_tool["description"] == "Add two numbers."
        # Should not have auth fields
        assert "auth_provider" not in add_tool
        assert "scopes" not in add_tool
        # Should not have default_interrupt or should be False
        assert add_tool.get("default_interrupt", False) is False

        # Check tool with auth - verify auth info is included
        auth_tool = next(t for t in tools if t["name"] == "test_auth_tool")
        assert auth_tool["description"].startswith(
            "A test tool that requires authentication."
        )
        # Should have auth fields
        assert "auth_provider" in auth_tool
        assert "scopes" in auth_tool
        assert auth_tool["auth_provider"] == "test_provider"
        assert auth_tool["scopes"] == ["test_scope"]
        # Should not have default_interrupt or should be False
        assert auth_tool.get("default_interrupt", False) is False

        # Check tool with default_interrupt=True
        interrupt_tool = next(t for t in tools if t["name"] == "sensitive_action")
        assert interrupt_tool["description"].startswith(
            "A test tool that should have interrupts enabled by default."
        )
        # Should not have auth fields
        assert "auth_provider" not in interrupt_tool
        assert "scopes" not in interrupt_tool
        # Should have default_interrupt=True
        assert "default_interrupt" in interrupt_tool
        assert interrupt_tool["default_interrupt"] is True

        # Test executing a non-auth tool
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "add", "arguments": {"x": 5, "y": 3}},
            },
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "result" in data
        assert data["result"]["content"][0]["type"] == "text"
        assert data["result"]["content"][0]["text"] == "8"


async def test_auth_toolkit_calls_custom_auth_on_all_endpoints():
    """Test that custom auth function is properly called across all endpoints."""
    test_dir = Path(__file__).parent.parent / "toolkits" / "auth"
    server = Server.from_toolkit(str(test_dir))

    # Import the auth module to access tracking variables
    # We need to import after server creation so the auth module is loaded
    auth_module_name = None
    for name, module in sys.modules.items():
        if hasattr(module, "AUTH_WAS_CALLED"):
            auth_module_name = name
            break

    assert auth_module_name is not None, "Auth module not found in sys.modules"
    auth_module = sys.modules[auth_module_name]

    # Reset tracking
    auth_module.reset_auth_tracking()
    assert not auth_module.AUTH_WAS_CALLED
    assert auth_module.AUTH_CALL_COUNT == 0

    # Create test client
    transport = ASGITransport(app=server, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # Test 1: HTTP REST API - List tools
        response = await client.get(
            "/tools", headers={"Authorization": "Bearer token1"}
        )
        assert response.status_code == 200
        assert auth_module.AUTH_WAS_CALLED
        assert auth_module.AUTH_CALL_COUNT == 1
        assert auth_module.LAST_AUTHORIZATION == "Bearer token1"

        # Verify tools are listed
        tools = response.json()
        assert len(tools) == 2
        assert tools[0]["name"] == "test_tool"

        # Test 2: HTTP REST API - Execute tool
        response = await client.post(
            "/tools/call",
            json={"request": {"tool_id": "test_tool", "input": {"message": "hello"}}},
            headers={"Authorization": "Bearer token2"},
        )
        assert response.status_code == 200
        assert auth_module.AUTH_CALL_COUNT == 2
        assert auth_module.LAST_AUTHORIZATION == "Bearer token2"

        # Verify tool execution result
        result = response.json()
        assert result["success"] is True
        assert result["value"] == "Test tool says: hello"

        # Test 3: MCP - List tools
        response = await client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Authorization": "Bearer token3"},
        )
        assert response.status_code == 200
        assert auth_module.AUTH_CALL_COUNT == 3
        assert auth_module.LAST_AUTHORIZATION == "Bearer token3"

        # Verify MCP tools list response
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        tools = data["result"]["tools"]
        assert len(tools) == 2
        assert tools[0]["name"] == "test_tool"

        # Test 4: MCP - Execute tool
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "test_tool", "arguments": {"message": "world"}},
            },
            headers={"Authorization": "Bearer token4"},
        )
        assert response.status_code == 200
        assert auth_module.AUTH_CALL_COUNT == 4
        assert auth_module.LAST_AUTHORIZATION == "Bearer token4"

        # Verify MCP tool execution result
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert data["result"]["content"][0]["type"] == "text"
        assert data["result"]["content"][0]["text"] == "Test tool says: world"


async def test_auth_toolkit_tracks_headers():
    """Test that custom auth properly tracks headers."""
    test_dir = Path(__file__).parent.parent / "toolkits" / "auth"
    server = Server.from_toolkit(str(test_dir))

    # Find auth module
    auth_module = None
    for _, module in sys.modules.items():
        if hasattr(module, "AUTH_WAS_CALLED"):
            auth_module = module
            break

    assert auth_module is not None
    auth_module.reset_auth_tracking()

    transport = ASGITransport(app=server, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # Make request with custom headers
        response = await client.post(
            "/tools/call",
            json={"request": {"tool_id": "test_tool", "input": {"message": "test"}}},
            headers={
                "Authorization": "Bearer custom_token",
                "Custom-Header": "custom_value",
            },
        )

        assert response.status_code == 200
        assert auth_module.AUTH_WAS_CALLED

        # Check that headers were tracked (they may be modified by middleware)
        assert auth_module.LAST_HEADERS is not None
        # The exact headers format may vary due to middleware, but authorization should be tracked
        assert auth_module.LAST_AUTHORIZATION == "Bearer custom_token"


async def test_auth_toolkit_calls_authenticate_with_correct_params():
    """Test tool that uses auth_provider and scopes calls authenticate with expected params."""
    test_dir = Path(__file__).parent.parent / "toolkits" / "auth"
    server = Server.from_toolkit(str(test_dir))

    # Set required environment variable
    with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test_api_key"}):
        # Mock the auth client
        with patch("langchain_auth.Client") as mock_client_class:
            # Create mock instances
            mock_client_instance = AsyncMock()
            mock_client_class.return_value = mock_client_instance

            # Mock successful auth (no additional OAuth needed)
            mock_auth_result = AsyncMock()
            mock_auth_result.needs_auth = False
            mock_auth_result.token = "test_oauth_token"
            mock_client_instance.authenticate.return_value = mock_auth_result

            transport = ASGITransport(app=server, raise_app_exceptions=True)
            async with AsyncClient(
                base_url="http://localhost", transport=transport
            ) as client:
                # Execute the tool with auth_provider
                response = await client.post(
                    "/tools/call",
                    json={
                        "request": {
                            "tool_id": "test_tool_with_auth_provider",
                            "input": {"message": "test"},
                        }
                    },
                    headers={"Authorization": "Bearer provider_token"},
                )

                assert response.status_code == 200

                # Verify the response includes the injected token and request
                result = response.json()
                assert result["success"] is True
                # Check that both token and request are present in the context
                assert "Token: test_oauth_token" in result["value"]
                assert "Message: test" in result["value"]
                assert "HasRequest: True" in result["value"]
                assert "Method: POST" in result["value"]

                # Verify authenticate was called with expected parameters
                mock_client_class.assert_called_once_with(api_key="test_api_key")
                mock_client_instance.authenticate.assert_called_once_with(
                    provider="my_provider",
                    scopes=["scopeA", "scopeB"],
                    user_id="test_user_provider_token",
                )


@pytest.mark.asyncio
async def test_mcp_toolkit_loads_native_and_mcp_tools_and_executes_them_correctly():
    """Test loading a toolkit with MCP servers configured."""

    # Test with the example MCP toolkit
    toolkit_path = Path(__file__).parent / "../toolkits/mcp_example"

    # Test sync toolkit loading
    sync_server = Server.from_toolkit(str(toolkit_path))
    assert len(sync_server.tool_handler.catalog) == 2, (
        f"Expected 2 native tools, got {len(sync_server.tool_handler.catalog)}"
    )

    # Test async toolkit loading with MCP servers
    async_server = await Server.afrom_toolkit(str(toolkit_path))

    # Should load native tools + MCP tools
    # 2 native + 4 math + 3 weather + 7 sse + 4 websocket = 20 tools
    assert len(async_server.tool_handler.catalog) == 20, (
        f"Expected 20 tools, got {len(async_server.tool_handler.catalog)}"
    )

    # Verify native tools are loaded
    assert "native_add" in async_server.tool_handler.catalog, (
        "native_add tool not found"
    )
    assert "native_multiply" in async_server.tool_handler.catalog, (
        "native_multiply tool not found"
    )

    # Verify math server tools (stdio transport)
    assert "math_server.add" in async_server.tool_handler.catalog, (
        "math_server.add not found"
    )
    assert "math_server.subtract" in async_server.tool_handler.catalog, (
        "math_server.subtract not found"
    )
    assert "math_server.multiply" in async_server.tool_handler.catalog, (
        "math_server.multiply not found"
    )
    assert "math_server.divide" in async_server.tool_handler.catalog, (
        "math_server.divide not found"
    )

    # Verify weather API tools (HTTP transport)
    assert "weather_api.get_weather" in async_server.tool_handler.catalog, (
        "weather_api.get_weather not found"
    )
    assert "weather_api.get_forecast" in async_server.tool_handler.catalog, (
        "weather_api.get_forecast not found"
    )
    assert "weather_api.convert_temperature" in async_server.tool_handler.catalog, (
        "weather_api.convert_temperature not found"
    )

    # Verify websocket tools (WebSocket transport)
    assert "websocket_server.validate_json" in async_server.tool_handler.catalog, (
        "websocket_server.validate_json not found"
    )
    assert "websocket_server.format_json" in async_server.tool_handler.catalog, (
        "websocket_server.format_json not found"
    )
    assert "websocket_server.minify_json" in async_server.tool_handler.catalog, (
        "websocket_server.minify_json not found"
    )
    assert "websocket_server.extract_keys" in async_server.tool_handler.catalog, (
        "websocket_server.extract_keys not found"
    )

    # Verify sse tools (SSE transport)
    assert "local_tools.hash_text" in async_server.tool_handler.catalog, (
        "local_tools.hash_text not found"
    )
    assert "local_tools.encode_base64" in async_server.tool_handler.catalog, (
        "local_tools.encode_base64 not found"
    )
    assert "local_tools.decode_base64" in async_server.tool_handler.catalog, (
        "local_tools.decode_base64 not found"
    )
    assert "local_tools.generate_uuid" in async_server.tool_handler.catalog, (
        "local_tools.generate_uuid not found"
    )
    assert "local_tools.get_timestamp" in async_server.tool_handler.catalog, (
        "local_tools.get_timestamp not found"
    )
    assert "local_tools.reverse_string" in async_server.tool_handler.catalog, (
        "local_tools.reverse_string not found"
    )
    assert "local_tools.count_words" in async_server.tool_handler.catalog, (
        "local_tools.count_words not found"
    )

    # Test native tool execution
    native_request = {"tool_id": "native_add", "input": {"x": 5, "y": 3}}
    native_result = await async_server.tool_handler.call_tool(native_request, None)
    assert native_result["success"], f"native_add failed: {native_result}"
    assert native_result["value"] == 8, f"Expected 8, got {native_result['value']}"

    # Test MCP tool execution - Math server (stdio)
    math_request = {"tool_id": "math_server.add", "input": {"x": 10, "y": 5}}
    math_result = await async_server.tool_handler.call_tool(math_request, None)
    assert math_result["success"], f"math_server.add failed: {math_result}"
    print(math_result)
    assert int(math_result["value"]) == 15, f"Expected 15, got {math_result['value']}"

    # Test weather API tool (HTTP transport)
    weather_request = {
        "tool_id": "weather_api.get_weather",
        "input": {"city": "London"},
    }
    weather_result = await async_server.tool_handler.call_tool(weather_request, None)
    assert weather_result["success"], (
        f"weather_api.get_weather failed: {weather_result}"
    )

    weather_data = json.loads(weather_result["value"])

    assert isinstance(weather_data, dict), (
        f"Expected dict result, got {type(weather_data)}"
    )
    assert "city" in weather_data, "Weather result missing 'city' field"
    assert weather_data["city"] == "London", (
        f"Expected London, got {weather_data['city']}"
    )

    # Test websocket tool execution
    websocket_request = {
        "tool_id": "websocket_server.validate_json",
        "input": {"json_string": '{"name": "John", "age": 30}'},
    }
    websocket_result = await async_server.tool_handler.call_tool(
        websocket_request, None
    )
    assert websocket_result["success"], (
        f"websocket_server.validate_json failed: {websocket_result}"
    )
    parsed_value = json.loads(websocket_result["value"])
    assert parsed_value == {"valid": True, "parsed": {"name": "John", "age": 30}}, (
        f"Expected {{'valid': True, 'parsed': {{'name': 'John', 'age': 30}}}}, got {parsed_value}"
    )

    # Test sse tool execution
    sse_request = {
        "tool_id": "local_tools.reverse_string",
        "input": {"text": "Hello, World!"},
    }
    sse_result = await async_server.tool_handler.call_tool(sse_request, None)
    assert sse_result["success"], f"local_tools.reverse_string failed: {sse_result}"
    assert sse_result["value"] == "!dlroW ,olleH", (
        f"Expected '!dlroW ,olleH', got {sse_result['value']}"
    )


def test_error_toolkit_tool_with_missing_type_annotation_raises_value_error():
    """Test that loading toolkit with missing type annotation raises ValueError."""
    # Get path to error test toolkit
    test_dir = Path(__file__).parent.parent / "toolkits" / "error"

    # Should raise ValueError when trying to create server with toolkit containing unannotated parameter
    with pytest.raises(ValueError) as exc_info:
        Server.from_toolkit(str(test_dir))

    # Verify error message is descriptive
    error_message = str(exc_info.value)
    assert "bad_tool" in error_message
    assert "Parameter 'param' missing type annotation" in error_message
    assert "All tool parameters must have type annotations" in error_message


async def test_inject_context_parameter_combinations():
    """Test all combinations of inject_context and auth_provider."""
    test_dir = Path(__file__).parent.parent / "toolkits" / "inject_context_test"
    server = Server.from_toolkit(str(test_dir))

    transport = ASGITransport(app=server, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.post(
            "/tools/call",
            json={
                "request": {
                    "tool_id": "tool_with_inject_context",
                    "input": {"message": "test"},
                }
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "message=test" in result["value"]
        assert "has_request=True" in result["value"]
        assert "has_token=False" in result["value"]
        assert "method=POST" in result["value"]

        response = await client.post(
            "/tools/call",
            json={
                "request": {
                    "tool_id": "tool_without_inject_context",
                    "input": {"message": "test"},
                }
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["value"] == "message=test"


def test_inject_context_false_with_context_param_raises_error():
    """Test that inject_context=False with context parameter raises ValueError."""
    from langchain_tool_server import Context, tool

    with pytest.raises(ValueError) as exc_info:

        @tool(inject_context=False)
        def bad_tool(context: Context, message: str) -> str:
            """Tool misconfigured with inject_context=False but has context param."""
            return message

    assert "inject_context is False" in str(exc_info.value)


def test_context_param_without_inject_context_raises_error():
    """Test that context parameter without inject_context raises ValueError."""
    from langchain_tool_server import Context, tool

    with pytest.raises(ValueError) as exc_info:

        @tool
        def bad_tool(context: Context, message: str) -> str:
            """Tool with context param but no inject_context or auth_provider."""
            return message

    assert "inject_context is False" in str(exc_info.value)


def test_inject_context_true_without_context_param_raises_error():
    """Test that inject_context=True without context parameter raises ValueError."""
    from langchain_tool_server import tool

    with pytest.raises(ValueError) as exc_info:

        @tool(inject_context=True)
        def bad_tool(message: str) -> str:
            """Tool with inject_context=True but no context parameter."""
            return message

    assert "inject_context=True but no 'context' parameter" in str(exc_info.value)
