"""
Simple Agent Example

A basic agent with 3 tools and no approval workflows.
Demonstrates: Basic tool usage, structured output

Run with: broadie chat examples/simple.py:agent
"""

from pydantic import BaseModel, Field

from broadie import ToolResponse, ToolStatus, create_agent, tool


# Tools
@tool(name="get_weather", parse_docstring=True)
def get_weather(location: str) -> ToolResponse:
    """Get current weather for a location.

    Args:
        location: City name or location to check weather for

    Returns:
        Weather information including temperature and conditions
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Weather retrieved for {location}",
        data={"location": location, "temp": 72, "conditions": "sunny"},
    )


@tool(name="search_news", parse_docstring=True)
def search_news(query: str) -> ToolResponse:
    """Search for recent news articles.

    Args:
        query: Search query for news articles

    Returns:
        List of news articles matching the query
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Found news for: {query}",
        data={"articles": [{"title": f"Latest on {query}", "source": "News Site"}]},
    )


@tool(name="calculate", parse_docstring=True)
def calculate(expression: str) -> ToolResponse:
    """Perform a mathematical calculation.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Calculation result
    """
    try:
        result = eval(expression)
        return ToolResponse(
            status=ToolStatus.SUCCESS,
            message=f"Calculated: {expression} = {result}",
            data={"expression": expression, "result": result},
        )
    except Exception as e:
        return ToolResponse(
            status=ToolStatus.ERROR,
            message=f"Calculation failed: {e}",
            data={"error": str(e)},
        )


# Output Schema
class SimpleOutput(BaseModel):
    summary: str = Field(description="Summary of the response")
    result: str = Field(description="Main result or answer")


# Create agent directly - works for both library and CLI usage
agent = create_agent(
    name="SimpleAgent",
    instruction=(
        "You are a helpful assistant with access to weather, news, and calculator tools. "
        "Provide clear, concise responses to user queries."
    ),
    tools=[get_weather, search_news, calculate],
    output_schema=SimpleOutput,
)
