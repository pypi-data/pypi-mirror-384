from langchain_tool_server import Context, tool


@tool
def hello() -> str:
    """Say hello."""
    return "Hello, world!"


@tool(default_interrupt=False)
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


@tool(auth_provider="test_provider", scopes=["test_scope"])
def test_auth_tool(context: Context, message: str) -> str:
    """A test tool that requires authentication.

    Args:
        context: Authentication context
        message: A message to echo

    Returns:
        The message with auth info
    """
    return f"Authenticated message: {message}"


@tool(default_interrupt=True)
def sensitive_action(action: str) -> str:
    """A test tool that should have interrupts enabled by default.

    Args:
        action: The action to perform

    Returns:
        Confirmation message
    """
    return f"Performed sensitive action: {action}"


TOOLS = [hello, add, test_auth_tool, sensitive_action]
