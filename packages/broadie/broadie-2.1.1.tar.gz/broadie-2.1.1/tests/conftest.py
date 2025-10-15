"""Pytest configuration and shared fixtures for broadie tests."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.broadie.agents import Agent
from src.broadie.persistence.manager import PersistenceManager
from src.broadie.schemas import AgentSchema, ModelProvider, ModelSchema
from src.broadie.tools.channels import ApiToolInput, EmailToolInput, SlackToolInput


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Configure database for testing - use in-memory SQLite or temp file."""
    # Check if we're in CI environment
    is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"

    if is_ci:
        # Use in-memory database for CI to avoid file system issues
        test_db_url = "sqlite+aiosqlite:///:memory:"
    else:
        # For local testing, use temp directory
        temp_dir = tempfile.gettempdir()
        test_db_path = Path(temp_dir) / "broadie_test.sqlite3"
        test_db_url = f"sqlite+aiosqlite:///{test_db_path}"

    # Set the DATABASE_URL environment variable for tests
    os.environ["DATABASE_URL"] = test_db_url

    yield test_db_url

    # Cleanup: remove test database file if it exists
    if not is_ci and "test_db_path" in locals():
        try:
            if test_db_path.exists():
                test_db_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture
def mock_agent():
    """Create a mock agent with necessary methods for testing."""
    agent = Mock()
    agent.id = "test_agent"
    agent.name = "test_agent"
    agent.model = ModelSchema(provider=ModelProvider.google, name="gemini-2.0-flash")

    # Mock async methods
    agent.run = AsyncMock(return_value={"result": "test response"})
    agent.remember_user_fact = AsyncMock(return_value="fact_id_123")
    agent.recall_user_facts = AsyncMock(return_value=[])
    agent.clear_user_facts = AsyncMock(return_value={"deleted": 0})
    agent.clear_thread_history = AsyncMock(return_value={"deleted": 0})

    # Mock store for memory operations
    agent.store = AsyncMock()
    agent.store.aput = AsyncMock()
    agent.store.alist = AsyncMock(return_value=[])
    agent.store.asearch = AsyncMock(return_value=[])

    return agent


@pytest.fixture
def mock_real_agent():
    """Create a real agent instance with mocked dependencies."""
    with patch("src.broadie.agents.create_react_agent") as mock_create_react:
        mock_runtime = AsyncMock()
        mock_message = Mock()
        mock_message.content = "Mocked response"
        mock_runtime.ainvoke.return_value = {"messages": [mock_message]}
        mock_create_react.return_value = mock_runtime

        config = AgentSchema(name="test_agent", instruction="Test instruction")
        agent = Agent(config)
        return agent


@pytest.fixture
def slack_tool_input():
    """Create a valid SlackToolInput for testing."""
    return SlackToolInput(channel="#test", blocks=None)


@pytest.fixture
def email_tool_input():
    """Create a valid EmailToolInput for testing."""
    return EmailToolInput(
        subject="Test Subject",
        body="Test Body",
        to="test@example.com",
    )


@pytest.fixture
def api_tool_input():
    """Create a valid ApiToolInput for testing."""
    return ApiToolInput(
        payload={"test": "data"},
        endpoint="https://api.test.com/webhook",
    )


@pytest.fixture
def mock_settings():
    """Mock settings with safe defaults for testing."""
    with patch("src.broadie.config.settings") as mock_settings:
        mock_settings.DATABASE_URL = "sqlite:///test.db"
        mock_settings.EMBEDDING_MODEL = "test-embedding-model"
        mock_settings.MEMORY_DECAY_MINUTES = 60
        mock_settings.HOST = "0.0.0.0"
        mock_settings.PORT = 8000
        mock_settings.DEBUG = False
        mock_settings.ENV = "dev"
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALLOWED_HOSTS = ["localhost", "0.0.0.0"]
        mock_settings.CORS_ORIGINS = []
        mock_settings.SLACK_BOT_TOKEN = None  # No token for most tests
        mock_settings.EMAIL_FROM = "test@example.com"
        mock_settings.SMTP_HOST = "localhost"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "test"
        mock_settings.SMTP_PASSWORD = "test"
        yield mock_settings


@pytest.fixture
def mock_langchain_tools():
    """Mock LangChain tool creation to prevent API calls."""
    with (
        patch("src.broadie.agents.create_react_agent") as mock_create,
        patch("src.broadie.agents.build_memory_tools") as mock_memory_tools,
    ):
        mock_runtime = AsyncMock()
        mock_message = Mock()
        mock_message.content = "Mocked response"
        mock_runtime.ainvoke.return_value = {"messages": [mock_message]}
        mock_create.return_value = mock_runtime

        # Mock memory tools to return empty list
        mock_memory_tools.return_value = []

        yield mock_create


@pytest.fixture(autouse=True)
def auto_mock_external_deps():
    """Auto-mock external dependencies that might cause network calls."""
    with (
        patch("requests.post") as mock_post,
        patch("smtplib.SMTP") as mock_smtp,
        patch("slack_sdk.WebClient") as mock_slack,
    ):
        # Mock requests
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        # Mock SMTP
        mock_smtp_instance = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        # Mock Slack
        mock_slack_instance = Mock()
        mock_slack_instance.chat_postMessage.return_value = {"ts": "123456.789"}
        mock_slack.return_value = mock_slack_instance

        yield {"requests": mock_post, "smtp": mock_smtp, "slack": mock_slack}


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for all tests."""
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="function", autouse=True)
def force_memory_mode():
    """Force all tests to use in-memory persistence to avoid event loop issues."""
    # Set environment variable before any agents are created
    original_env = os.environ.get("ENV")
    os.environ["ENV"] = "test"

    yield

    # Restore original environment
    if original_env is not None:
        os.environ["ENV"] = original_env
    else:
        os.environ.pop("ENV", None)


@pytest.fixture(scope="function")
async def persistence_manager() -> AsyncGenerator[PersistenceManager, None]:
    """Provide a clean persistence manager for each test."""
    os.environ["ENV"] = "test"
    manager = PersistenceManager(use_memory=True)
    await manager.initialize()

    yield manager

    # Cleanup
    await manager.close()


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment for each test."""
    os.environ["ENV"] = "test"
    yield
    # Cleanup after test
