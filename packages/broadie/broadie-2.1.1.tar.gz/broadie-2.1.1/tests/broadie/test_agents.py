from unittest.mock import AsyncMock, Mock

import pytest

from src.broadie.agents import Agent
from src.broadie.schemas import AgentSchema, ModelProvider, ModelSchema


@pytest.fixture(autouse=True)
def mock_graph():
    """Auto-mock the graph for unit tests."""
    mock = AsyncMock()
    mock_message = Mock()
    mock_message.content = "Mocked response"
    mock.ainvoke.return_value = {"messages": [mock_message]}
    return mock


class TestAgent:
    """Unit tests for Agent class."""

    def test_agent_initialization_minimal(self, mock_graph):
        """Test Agent initialization with minimal configuration."""
        config = AgentSchema(name="test_agent", instruction="Be helpful")
        agent = Agent(config, mock_graph)

        assert agent.name == "test_agent"
        assert agent.config.instruction == "Be helpful"
        assert agent.id is not None

    def test_agent_initialization_with_model(self, mock_graph):
        """Test Agent initialization with custom model."""
        model = ModelSchema(provider=ModelProvider.google, name="gemini-2.0-flash")
        config = AgentSchema(name="test_agent", instruction="Be helpful", model=model)
        agent = Agent(config, mock_graph)

        assert agent.model == model

    def test_agent_initialization_with_tools(self, mock_graph):
        """Test Agent initialization with tools."""

        def custom_tool():
            """A custom tool."""
            return "result"

        config = AgentSchema(name="test_agent", instruction="Be helpful", tools=[custom_tool])
        agent = Agent(config, mock_graph)

        assert custom_tool in agent.tools

    @pytest.mark.asyncio
    async def test_agent_run_basic(self, mock_graph):
        """Test Agent run method."""
        config = AgentSchema(name="test_agent", instruction="Be helpful")
        agent = Agent(config, mock_graph)

        mock_message = Mock()
        mock_message.content = "Test response"
        mock_graph.astream.return_value = AsyncMock()
        mock_graph.astream.return_value.__aiter__.return_value = [{"messages": [mock_message]}]

        result = await agent.run("Test input")

        assert result is not None

    def test_agent_has_required_attributes(self, mock_graph):
        """Test Agent has required attributes."""
        config = AgentSchema(name="test_agent", instruction="Be helpful")
        agent = Agent(config, mock_graph)

        assert hasattr(agent, "name")
        assert hasattr(agent, "id")
        assert hasattr(agent, "config")
        assert hasattr(agent, "model")
        assert hasattr(agent, "tools")
