from fastapi import Request

from broadie.config import settings


def extract_capabilities(agent) -> list[dict]:
    """
    Extract capabilities from agent's tools.

    Works with the new Agent wrapper that stores tools in agent.tools (list).
    """
    capabilities = []

    # Handle new Agent class structure (tools stored in agent.tools)
    tools = getattr(agent, "tools", [])

    for tool in tools:
        # Handle different tool formats (LangChain tools, callable functions, etc.)
        tool_name = None
        tool_description = None

        # Try different ways to get tool name
        if hasattr(tool, "name"):
            tool_name = tool.name
        elif hasattr(tool, "__name__"):
            tool_name = tool.__name__
        elif hasattr(tool, "get_name") and callable(tool.get_name):
            tool_name = tool.get_name()
        else:
            tool_name = str(tool)

        # Try different ways to get tool description
        if hasattr(tool, "description"):
            tool_description = tool.description
        elif hasattr(tool, "__doc__"):
            tool_description = tool.__doc__ or ""
        else:
            tool_description = ""

        capabilities.append(
            {
                "capability": tool_name,
                "tool_name": tool_name,
                "description": tool_description.strip() if isinstance(tool_description, str) else "",
            },
        )

    return capabilities


def verify_auth(request: Request) -> bool:
    """Check Authorization header against configured secret."""
    if not settings.A2A_ENABLED:
        return True  # no auth needed if disabled (dev mode)

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False

    # Expect: Authorization: Bearer <secret>
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        return False

    return token.strip() == settings.A2A_REGISTRY_SECRET
