from langchain_tool_server import Context, tool


@tool(inject_context=True)
def tool_with_inject_context(context: Context, message: str) -> str:
    """Tool with inject_context=True and no auth_provider."""
    has_request = context.request is not None
    has_token = context.token is not None
    request_method = context.request.method if has_request else "None"
    return f"message={message}, has_request={has_request}, has_token={has_token}, method={request_method}"


@tool
def tool_without_inject_context(message: str) -> str:
    """Tool without inject_context (default behavior)."""
    return f"message={message}"


TOOLS = [tool_with_inject_context, tool_without_inject_context]
