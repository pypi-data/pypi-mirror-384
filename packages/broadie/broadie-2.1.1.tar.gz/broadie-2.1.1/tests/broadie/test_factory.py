from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel, Field

from src.broadie.factory import _build_channels, create_agent
from src.broadie.schemas import ChannelSchema, ChannelType, ModelProvider, ModelSchema


class CustomOutput(BaseModel):
    """Custom output schema for testing."""

    result: str = Field(description="The result")
    status: str = Field(description="The status")


class TestBuildChannels:
    """Unit tests for _build_channels function."""

    def test_build_channels_empty_list(self):
        """Test _build_channels with empty list."""
        result = _build_channels([])
        assert result == []

    def test_build_channels_none(self):
        """Test _build_channels with None."""
        result = _build_channels(None)
        assert result == []

    def test_build_channels_with_channel_schema(self):
        """Test _build_channels with ChannelSchema objects."""
        channels = [
            ChannelSchema(type=ChannelType.slack, target="#general"),
            ChannelSchema(type=ChannelType.email, target="user@example.com"),
        ]
        result = _build_channels(channels)

        assert len(result) == 2
        assert all(isinstance(ch, ChannelSchema) for ch in result)
        assert result[0].type == ChannelType.slack
        assert result[1].type == ChannelType.email

    def test_build_channels_with_dict(self):
        """Test _build_channels with dictionary objects."""
        channels = [
            {"type": "slack", "target": "#general", "instructions": "Format nicely"},
            {"type": "email", "target": "admin@example.com"},
        ]
        result = _build_channels(channels)

        assert len(result) == 2
        assert all(isinstance(ch, ChannelSchema) for ch in result)
        assert result[0].type == ChannelType.slack
        assert result[0].target == "#general"
        assert result[0].instructions == "Format nicely"
        assert result[1].type == ChannelType.email
        assert result[1].target == "admin@example.com"

    def test_build_channels_invalid_type(self):
        """Test _build_channels with invalid channel type."""
        channels = ["invalid_channel"]

        with pytest.raises(ValueError, match="Invalid channel type"):
            _build_channels(channels)


class TestCreateAgent:
    """Unit tests for create_agent function."""

    @pytest.mark.asyncio
    async def test_create_agent_minimal(self):
        """Test create_agent with minimal parameters."""
        with (
            patch("src.broadie.factory.PersistenceManager") as mock_persistence_class,
            patch("src.broadie.factory.build_single_agent_graph") as mock_build_graph,
        ):
            mock_persistence = AsyncMock()
            mock_persistence.initialize = AsyncMock()
            mock_persistence.checkpointer = AsyncMock()
            mock_persistence.store = AsyncMock()
            mock_persistence_class.return_value = mock_persistence

            mock_graph = AsyncMock()
            mock_build_graph.return_value = mock_graph

            agent = await create_agent(name="test_agent", instruction="Be helpful")

            # create_agent returns LazyAgent, not Agent directly
            from src.broadie.factory import LazyAgent

            assert isinstance(agent, LazyAgent)
            assert agent.name == "test_agent"
            assert agent._instruction == "Be helpful"

    @pytest.mark.asyncio
    async def test_create_agent_with_model(self):
        """Test create_agent with custom model."""
        with (
            patch("src.broadie.factory.PersistenceManager") as mock_persistence_class,
            patch("src.broadie.factory.build_single_agent_graph") as mock_build_graph,
        ):
            mock_persistence = AsyncMock()
            mock_persistence.initialize = AsyncMock()
            mock_persistence.checkpointer = AsyncMock()
            mock_persistence.store = AsyncMock()
            mock_persistence_class.return_value = mock_persistence

            mock_graph = AsyncMock()
            mock_build_graph.return_value = mock_graph

            model = ModelSchema(provider=ModelProvider.google, name="gemini-2.0-flash")
            agent = await create_agent(name="test_agent", instruction="Be helpful", model=model)

            assert agent.model == model

    @pytest.mark.asyncio
    async def test_create_agent_with_tools(self):
        """Test create_agent with tools."""

        def custom_tool():
            """A custom tool."""
            return "result"

        with (
            patch("src.broadie.factory.PersistenceManager") as mock_persistence_class,
            patch("src.broadie.factory.build_single_agent_graph") as mock_build_graph,
        ):
            mock_persistence = AsyncMock()
            mock_persistence.initialize = AsyncMock()
            mock_persistence.checkpointer = AsyncMock()
            mock_persistence.store = AsyncMock()
            mock_persistence_class.return_value = mock_persistence

            mock_graph = AsyncMock()
            mock_build_graph.return_value = mock_graph

            agent = await create_agent(name="test_agent", instruction="Be helpful", tools=[custom_tool])

            assert custom_tool in agent.tools
