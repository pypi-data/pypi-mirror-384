import pytest
from pydantic import BaseModel, Field, ValidationError

from src.broadie.schemas import AgentSchema, ChannelSchema, ChannelType, ModelProvider, ModelSchema


class AgentOutput(BaseModel):
    """Test output schema for Agent."""

    result: str = Field(description="The result of the operation")


class TestModelProvider:
    """Test cases for ModelProvider enum."""

    def test_model_provider_values(self):
        """Test all ModelProvider enum values."""
        assert ModelProvider.google == "google_vertexai"
        assert ModelProvider.openai == "openai"
        assert ModelProvider.anthropic == "anthropic"
        assert ModelProvider.ollama == "ollama"
        assert ModelProvider.custom == "custom"

    def test_model_provider_string_comparison(self):
        """Test ModelProvider string comparison."""
        assert ModelProvider.google == "google_vertexai"
        assert str(ModelProvider.google.lower()) == "google_vertexai"

    def test_model_provider_all_values(self):
        """Test all enum values are accessible."""
        expected_values = {"google_vertexai", "openai", "anthropic", "ollama", "custom"}
        actual_values = {provider.value for provider in ModelProvider}
        assert actual_values == expected_values


class TestModelSchema:
    """Test cases for ModelSchema."""

    def test_model_schema_defaults(self):
        """Test ModelSchema default values."""
        model = ModelSchema()
        assert model.provider == ModelProvider.google
        assert model.name == "gemini-2.0-flash"
        assert model.settings == {}

    def test_model_schema_custom_values(self):
        """Test ModelSchema with custom values."""
        settings = {"temperature": 0.5, "max_tokens": 1000}
        model = ModelSchema(
            provider=ModelProvider.openai,
            name="gpt-4",
            settings=settings,
        )
        assert model.provider == ModelProvider.openai
        assert model.name == "gpt-4"
        assert model.settings == settings

    def test_model_schema_provider_validation(self):
        """Test ModelSchema provider validation."""
        # Valid provider
        model = ModelSchema(provider=ModelProvider.anthropic)
        assert model.provider == ModelProvider.anthropic

        # Invalid provider should raise ValidationError
        with pytest.raises(ValidationError):
            ModelSchema(provider="invalid_provider")

    def test_model_schema_json_serialization(self):
        """Test ModelSchema JSON serialization."""
        model = ModelSchema(
            provider=ModelProvider.openai,
            name="gpt-4",
            settings={"temperature": 0.7},
        )
        json_data = model.model_dump()
        assert json_data["provider"] == "openai"
        assert json_data["name"] == "gpt-4"
        assert json_data["settings"] == {"temperature": 0.7}


class TestChannelType:
    """Test cases for ChannelType enum."""

    def test_channel_type_values(self):
        """Test all ChannelType enum values."""
        assert ChannelType.slack == "slack"
        assert ChannelType.api == "api"
        assert ChannelType.email == "email"

    def test_channel_type_all_values(self):
        """Test all enum values are accessible."""
        expected_values = {"slack", "api", "email"}
        actual_values = {channel_type.value for channel_type in ChannelType}
        assert actual_values == expected_values


class TestChannelSchema:
    """Test cases for ChannelSchema."""

    def test_channel_schema_minimal(self):
        """Test ChannelSchema with minimal fields."""
        channel = ChannelSchema(type=ChannelType.slack, target="#general")
        assert channel.type == ChannelType.slack
        assert channel.target == "#general"
        assert channel.instructions is None

    def test_channel_schema_with_instructions(self):
        """Test ChannelSchema with instructions."""
        channel = ChannelSchema(type=ChannelType.email, target="user@example.com", instructions="Format as markdown")
        assert channel.instructions == "Format as markdown"


class TestAgentSchema:
    """Test cases for AgentSchema."""

    def test_agent_schema_minimal(self):
        """Test AgentSchema with minimal required fields."""
        agent = AgentSchema(name="test_agent", instruction="Be helpful")
        assert agent.name == "test_agent"
        assert agent.instruction == "Be helpful"
        assert agent.tools == []

    def test_agent_schema_with_model(self):
        """Test AgentSchema with custom model."""
        model = ModelSchema(provider=ModelProvider.openai, name="gpt-4")
        agent = AgentSchema(name="test", instruction="Help", model=model)
        assert agent.model == model

    def test_agent_schema_with_tools(self):
        """Test AgentSchema with tools."""

        def tool1():
            return "result1"

        agent = AgentSchema(name="test", instruction="Help", tools=[tool1])
        assert len(agent.tools) == 1
        assert callable(agent.tools[0])
