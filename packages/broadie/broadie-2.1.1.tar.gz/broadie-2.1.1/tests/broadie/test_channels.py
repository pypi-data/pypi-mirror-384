from unittest.mock import AsyncMock, patch

import pytest

from src.broadie.channels import ChannelsAgent
from src.broadie.schemas import ChannelSchema, ChannelType, ModelProvider, ModelSchema


class TestChannelsAgent:
    """Unit tests for ChannelsAgent class."""

    @pytest.fixture
    def mock_create_react_agent(self):
        """Mock create_react_agent to prevent API calls."""
        with patch("src.broadie.channels.create_react_agent") as mock_create:
            mock_runtime = AsyncMock()
            mock_runtime.ainvoke.return_value = {"messages": [{"content": "Delivered"}]}
            mock_create.return_value = mock_runtime
            yield mock_create

    @pytest.fixture
    def sample_model(self):
        """Sample ModelSchema for testing."""
        return ModelSchema(provider=ModelProvider.google, name="gemini-2.0-flash")

    @pytest.fixture
    def sample_channel(self):
        """Sample ChannelSchema for testing."""
        return ChannelSchema(
            type=ChannelType.slack,
            target="#general",
            instructions="Send as a formatted message",
        )

    def test_channels_agent_init(self, mock_create_react_agent, sample_model):
        """Test ChannelsAgent initialization."""
        agent = ChannelsAgent(sample_model)

        assert agent.model == sample_model
        assert agent.runtime is not None
        mock_create_react_agent.assert_called_once()

    def test_channels_agent_init_runtime(self, mock_create_react_agent, sample_model):
        """Test ChannelsAgent runtime initialization with correct parameters."""
        agent = ChannelsAgent(sample_model)  # noqa

        # Verify create_react_agent was called with correct parameters
        call_args = mock_create_react_agent.call_args
        assert call_args[1]["model"] == "google_vertexai:gemini-2.0-flash"
        assert len(call_args[1]["tools"]) == 3
        assert "delivery assistant" in call_args[1]["prompt"].lower()

    def test_channels_agent_init_with_different_model(self, mock_create_react_agent):
        """Test ChannelsAgent initialization with different model provider."""
        model = ModelSchema(provider=ModelProvider.openai, name="gpt-4")
        agent = ChannelsAgent(model)  # noqa

        call_args = mock_create_react_agent.call_args
        assert call_args[1]["model"] == "openai:gpt-4"

    @pytest.mark.asyncio
    async def test_channels_agent_run(
        self,
        mock_create_react_agent,
        sample_model,
        sample_channel,
    ):
        """Test ChannelsAgent run method."""
        agent = ChannelsAgent(sample_model)

        output = {"result": "Test message"}
        thread_id = "thread-123"
        message_id = "msg-123"
        run_id = "run-123"

        result = await agent.run(sample_channel, output, thread_id, message_id, run_id)

        # Verify runtime.ainvoke was called
        mock_runtime = mock_create_react_agent.return_value
        mock_runtime.ainvoke.assert_called_once()

        # Verify the result
        assert result == {"messages": [{"content": "Delivered"}]}

    @pytest.mark.asyncio
    async def test_channels_agent_run_command_structure(
        self,
        mock_create_react_agent,
        sample_model,
        sample_channel,
    ):
        """Test ChannelsAgent run method Command structure."""
        agent = ChannelsAgent(sample_model)

        output = {"result": "Test message"}
        thread_id = "thread-123"
        message_id = "msg-123"
        run_id = "run-123"

        await agent.run(sample_channel, output, thread_id, message_id, run_id)

        # Get the call arguments
        mock_runtime = mock_create_react_agent.return_value
        call_args = mock_runtime.ainvoke.call_args

        # Verify Command structure
        command = call_args[0][0]
        assert hasattr(command, "update")
        assert "messages" in command.update
        assert len(command.update["messages"]) == 1

        message = command.update["messages"][0]
        assert message["role"] == "user"
        assert message["id"] == message_id
        assert sample_channel.type.value in message["content"]
        assert sample_channel.target in message["content"]

    @pytest.mark.asyncio
    async def test_channels_agent_run_config_structure(
        self,
        mock_create_react_agent,
        sample_model,
        sample_channel,
    ):
        """Test ChannelsAgent run method config structure."""
        agent = ChannelsAgent(sample_model)

        output = {"result": "Test message"}
        thread_id = "thread-123"
        message_id = "msg-123"
        run_id = "run-123"

        await agent.run(sample_channel, output, thread_id, message_id, run_id)

        # Get the call arguments
        mock_runtime = mock_create_react_agent.return_value
        call_args = mock_runtime.ainvoke.call_args

        # Verify config structure
        config = call_args[1]["config"]
        assert config["configurable"]["thread_id"] == thread_id
        assert config["run_id"] == run_id
        assert config["metadata"]["channel"] == sample_channel.type
        assert config["metadata"]["target"] == sample_channel.target

    @pytest.mark.asyncio
    async def test_channels_agent_run_with_no_instructions(
        self,
        mock_create_react_agent,
        sample_model,
    ):
        """Test ChannelsAgent run method with channel having no instructions."""
        agent = ChannelsAgent(sample_model)

        channel = ChannelSchema(type=ChannelType.email, target="user@example.com")
        output = {"result": "Test message"}
        thread_id = "thread-123"
        message_id = "msg-123"
        run_id = "run-123"

        await agent.run(channel, output, thread_id, message_id, run_id)

        # Get the call arguments
        mock_runtime = mock_create_react_agent.return_value
        call_args = mock_runtime.ainvoke.call_args

        message = call_args[0][0].update["messages"][0]
        assert "Channel instructions: None" in message["content"]

    @pytest.mark.asyncio
    async def test_channels_agent_run_different_channel_types(
        self,
        mock_create_react_agent,
        sample_model,
    ):
        """Test ChannelsAgent run method with different channel types."""
        agent = ChannelsAgent(sample_model)
        output = {"result": "Test message"}
        thread_id = "thread-123"
        message_id = "msg-123"
        run_id = "run-123"

        # Test Slack channel
        slack_channel = ChannelSchema(type=ChannelType.slack, target="#general")
        await agent.run(slack_channel, output, thread_id, message_id, run_id)

        # Test Email channel
        email_channel = ChannelSchema(type=ChannelType.email, target="user@example.com")
        await agent.run(email_channel, output, thread_id, message_id, run_id)

        # Test API channel
        api_channel = ChannelSchema(
            type=ChannelType.api,
            target="https://api.example.com/webhook",
        )
        await agent.run(api_channel, output, thread_id, message_id, run_id)

        # Verify all calls were made
        mock_runtime = mock_create_react_agent.return_value
        assert mock_runtime.ainvoke.call_count == 3

    @pytest.mark.asyncio
    async def test_channels_agent_run_with_complex_output(
        self,
        mock_create_react_agent,
        sample_model,
        sample_channel,
    ):
        """Test ChannelsAgent run method with complex output data."""
        agent = ChannelsAgent(sample_model)

        complex_output = {
            "result": "Complex result",
            "data": {"items": [1, 2, 3], "metadata": {"processed": True}},
            "status": "success",
        }

        await agent.run(
            sample_channel,
            complex_output,
            "thread-123",
            "msg-123",
            "run-123",
        )

        # Get the call arguments and verify complex output is included
        mock_runtime = mock_create_react_agent.return_value
        call_args = mock_runtime.ainvoke.call_args

        message = call_args[0][0].update["messages"][0]
        assert str(complex_output) in message["content"]

    def test_channels_agent_tools_included(self, mock_create_react_agent, sample_model):
        """Test that ChannelsAgent includes all required tools."""
        agent = ChannelsAgent(sample_model)  # noqa

        call_args = mock_create_react_agent.call_args
        tools = call_args[1]["tools"]

        # Check that we have 3 tools and they have the expected names
        assert len(tools) == 3
        tool_names = {tool.name for tool in tools}
        expected_names = {"send_slack_tool", "send_email_tool", "send_api_tool"}
        assert tool_names == expected_names
