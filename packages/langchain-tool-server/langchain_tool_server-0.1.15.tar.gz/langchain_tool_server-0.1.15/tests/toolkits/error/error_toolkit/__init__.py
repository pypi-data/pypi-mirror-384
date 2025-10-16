from langchain_tool_server import tool


@tool
def bad_tool(param):
    """A tool with missing type annotation on parameter."""
    return f"Got: {param}"


TOOLS = [bad_tool]
