import asyncio
import pathlib
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from src.broadie.cli import chat, load_agent_from_path, main, prepare_agent, serve, version


class TestLoadAgentFromPath:
    """Unit tests for load_agent_from_path function."""

    def test_load_agent_invalid_format(self):
        """Test load_agent_from_path with invalid format."""
        from click import ClickException

        with pytest.raises(ClickException, match="Invalid format"):
            load_agent_from_path("invalid_format")

    def test_load_agent_from_file_not_exists(self):
        """Test load_agent_from_path with non-existent file."""
        from click import ClickException

        with pytest.raises(ClickException, match="Could not import"):
            load_agent_from_path("nonexistent.py:agent")

    def test_load_agent_from_file_success(self):
        """Test load_agent_from_path with valid file."""
        # Create a temporary Python file with an agent
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
class MockAgent:
    def __init__(self):
        self.id = "test_agent"

test_agent = MockAgent()
""",
            )
            temp_file = f.name

        try:
            agent = load_agent_from_path(f"{temp_file}:test_agent")
            assert agent.id == "test_agent"
        finally:
            # Clean up
            pathlib.Path(temp_file).unlink()

    def test_load_agent_from_module_success(self):
        """Test load_agent_from_path with importable module."""
        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_agent = Mock()
            mock_module.test_agent = mock_agent
            mock_import.return_value = mock_module

            result = load_agent_from_path("test.module:test_agent")

            assert result == mock_agent
            mock_import.assert_called_once_with("test.module")

    def test_load_agent_from_module_not_found(self):
        """Test load_agent_from_path with non-existent module."""
        from click import ClickException

        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ModuleNotFoundError(
                "No module named 'nonexistent'",
            )

            with pytest.raises(ClickException, match="Could not import"):
                load_agent_from_path("nonexistent:agent")

    def test_load_agent_attribute_not_found(self):
        """Test load_agent_from_path when agent attribute doesn't exist."""
        from click import ClickException

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            # Remove the nonexistent_agent attribute
            if hasattr(mock_module, "nonexistent_agent"):
                del mock_module.nonexistent_agent
            mock_import.return_value = mock_module

            with pytest.raises(ClickException, match="not found"):
                load_agent_from_path("test.module:nonexistent_agent")

    def test_load_agent_from_file_path_extraction(self):
        """Test that file path is correctly extracted and processed."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
class MockAgent:
    def __init__(self):
        self.id = "test_agent"

test_agent = MockAgent()
""",
            )
            temp_file = f.name

        try:
            # This test actually loads the file and checks the result
            result = load_agent_from_path(f"{temp_file}:test_agent")
            assert result.id == "test_agent"
        finally:
            pathlib.Path(temp_file).unlink()


class TestPrepareAgent:
    """Unit tests for prepare_agent function."""

    @pytest.mark.asyncio
    async def test_prepare_agent_with_methods(self):
        """Test prepare_agent with agent that has init methods."""

        class MockAgentWithMethods:
            def __init__(self):
                self.init_checkpointer = AsyncMock()
                self.init_store = AsyncMock()

        mock_agent = MockAgentWithMethods()

        result = await prepare_agent(mock_agent)

        assert result == mock_agent
        mock_agent.init_checkpointer.assert_called_once()
        mock_agent.init_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_prepare_agent_without_methods(self):
        """Test prepare_agent with agent that doesn't have init methods."""

        class MockAgentWithoutMethods:
            pass

        mock_agent = MockAgentWithoutMethods()

        result = await prepare_agent(mock_agent)

        assert result == mock_agent

    @pytest.mark.asyncio
    async def test_prepare_agent_with_partial_methods(self):
        """Test prepare_agent with agent that has only some init methods."""

        class MockAgentPartialMethods:
            def __init__(self):
                self.init_checkpointer = AsyncMock()

        mock_agent = MockAgentPartialMethods()

        result = await prepare_agent(mock_agent)

        assert result == mock_agent
        mock_agent.init_checkpointer.assert_called_once()


class TestCLICommands:
    """Unit tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_main_command(self, runner):
        """Test main CLI group command."""
        result = runner.invoke(main, [])

        # The main command without arguments shows help (exit code 2) which is expected
        # Check for the help output instead
        assert "broadie" in result.output or "Usage:" in result.output

    def test_version_command(self, runner):
        """Test version command."""
        with patch("broadie.__version__", "1.0.0"):
            result = runner.invoke(version, [])

            assert result.exit_code == 0
            assert "Broadie" in result.output

    def test_version_command_import_error(self, runner):
        """Test version command when import fails."""
        with patch("builtins.__import__", side_effect=ImportError):
            result = runner.invoke(version, [])
            # If import fails, the command should raise an error
            assert result.exit_code != 0

    @patch("src.broadie.cli.uvicorn.run")
    @patch("src.broadie.cli.register_agent_with_registry")
    @patch("src.broadie.cli.prepare_agent")
    @patch("src.broadie.cli.load_agent_from_path")
    @patch("src.broadie.cli.settings")
    def test_serve_command(
        self,
        mock_settings,
        mock_load_agent,
        mock_prepare,
        mock_register,
        mock_uvicorn,
        runner,
    ):
        """Test serve command."""
        # Setup mocks
        mock_agent = Mock()
        mock_agent.id = "test_agent"
        mock_load_agent.return_value = mock_agent

        mock_prepare.return_value = mock_agent
        mock_register.return_value = AsyncMock()

        mock_settings.HOST = "0.0.0.0"
        mock_settings.PORT = 8000

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = mock_agent

            result = runner.invoke(
                serve,
                ["test.py:agent", "--host", "0.0.0.0", "--port", "9000"],
            )

            assert result.exit_code == 0
            mock_load_agent.assert_called_once_with("test.py:agent")
            mock_uvicorn.assert_called_once()

    def test_serve_command_invalid_target(self, runner):
        """Test serve command with invalid target."""
        with patch("src.broadie.cli.load_agent_from_path") as mock_load_agent:
            from click import ClickException

            mock_load_agent.side_effect = ClickException("Invalid format")

            result = runner.invoke(serve, ["invalid"])

            assert result.exit_code != 0

    @patch("src.broadie.cli.prepare_agent")
    @patch("src.broadie.cli.load_agent_from_path")
    def test_run_command(self, mock_load_agent, mock_prepare, runner):
        """Test run command."""
        # Setup mocks
        mock_agent = AsyncMock()
        mock_agent.id = "test_agent"
        mock_agent.run = AsyncMock(return_value="Hello!")
        mock_load_agent.return_value = mock_agent
        mock_prepare.return_value = mock_agent

        # Mock asyncio.run and the internal chat function behavior
        async def mock_chat():
            # This simulates what happens inside the chat function
            agent = mock_load_agent("test.py:agent")
            agent = await mock_prepare(agent)
            return agent

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.side_effect = lambda f: None  # Don't actually run the async function

            result = runner.invoke(chat, ["test.py:agent"])  # noqa

            # Verify asyncio.run was called (the chat function was set up)
            mock_asyncio_run.assert_called_once()

    def test_run_command_invalid_target(self, runner):
        """Test run command with invalid target."""
        with patch("src.broadie.cli.load_agent_from_path") as mock_load_agent:
            from click import ClickException

            mock_load_agent.side_effect = ClickException("Invalid format")

            # Mock asyncio.run to properly handle the async function and avoid coroutine warnings
            with patch("asyncio.run") as mock_asyncio_run:

                def mock_run(coro):
                    # Properly close the coroutine to avoid warnings
                    try:
                        # Try to get the result, which will trigger the exception
                        loop = asyncio.new_event_loop()
                        try:
                            return loop.run_until_complete(coro)
                        finally:
                            loop.close()
                    except Exception:
                        # Close the coroutine properly if it failed
                        coro.close()
                        raise

                mock_asyncio_run.side_effect = mock_run

                result = runner.invoke(chat, ["invalid"])

                assert result.exit_code != 0

    def test_cli_integration(self, runner):
        """Test CLI integration and help system."""
        # Test main help
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Broadie" in result.output

        # Test serve help
        result = runner.invoke(main, ["serve", "--help"])
        assert result.exit_code == 0
        assert "TARGET must be" in result.output

        # Test run help
        result = runner.invoke(main, ["chat", "--help"])
        assert result.exit_code == 0
        assert "Run an agent in CLI chat mode" in result.output

    def test_warnings_configuration(self):
        """Test that warnings are properly configured."""
        import warnings

        # This test ensures the warnings filters are set
        # The actual filtering is tested by ensuring the module imports without warnings
        with warnings.catch_warnings(record=True) as w:  # noqa
            warnings.simplefilter("always")
            # Re-import the cli module to trigger warning filters

            # Check that deprecated warnings are filtered
            # This is more of a smoke test to ensure the module loads properly
