from broadie import create_agent

# CONTRIBUTION.md

## Welcome to broadie - Production-Grade AI Agent Framework

**Repository:** https://github.com/broadinstitute/broadie

broadie is an opinionated, production-ready framework for building and deploying AI agents with enterprise-grade reliability. This framework provides tools to interact with agents through well-defined schemas and contracts, with built-in support for communication channels (Slack, email, API), agent registry, and extensible tooling.

## 🏗️ Architecture Overview

broadie follows a modular architecture designed for scalability and maintainability:

```
broadie/
├── agents.py          # Core agent classes (Agent, SubAgent, BaseAgent)
├── factory.py         # Factory functions for creating agents
├── schemas.py         # Pydantic schemas and data models
├── config.py          # Configuration management
├── channels.py        # Channel agent for message delivery
├── mixins.py          # Persistence and memory mixins
├── prompts.py         # Base prompts and instructions
├── utils.py           # Utility functions
├── cli.py             # Command-line interface
├── server/            # FastAPI server components
├── tools/             # Agent tools and capabilities
└── a2a/               # Agent-to-Agent communication
```

## 🧩 Core Components

### 1. Agents (`agents.py`)

The heart of the framework - intelligent entities that can reason and act:

- **`BaseAgent`**: Abstract base class defining the agent interface
- **`Agent`**: Main agent implementation with full capabilities
- **`SubAgent`**: Specialized agents for specific tasks

```python
from broadie import create_agent

agent = create_agent(
    name="customer_support",
    instruction="You are a helpful customer support agent",
    tools=["send_email", "lookup_order"],
    channels=[{"type": "slack", "target": "#support"}]
)
```

### 2. Factory Functions (`factory.py`)

Simplified agent creation with sensible defaults:

- **`create_agent()`**: Create a full-featured agent
- **`create_sub_agent()`**: Create a specialized sub-agent

### 3. Schemas (`schemas.py`)

Type-safe data models using Pydantic:

- **`AgentSchema`**: Agent configuration and metadata
- **`SubAgentSchema`**: Sub-agent configuration
- **`ModelSchema`**: LLM model specifications
- **`ChannelSchema`**: Communication channel definitions

### 4. Tools (`tools/`)

Extensible capabilities that agents can use:

#### Memory Tools (`tools/memory.py`)
- `remember_fact`: Store user information long-term
- `recall_facts`: Retrieve stored information
- `save_message`: Store conversation history
- `get_history`: Retrieve conversation history

#### Channel Tools (`tools/channels.py`)
- `send_slack_tool`: Send messages to Slack channels
- `send_email_tool`: Send email notifications
- `send_api_tool`: Make API calls to external services

#### Task Tools (`tools/tasks.py`)
- `create_tasks`: Initialize task lists for threads
- `update_task`: Manage task completion status

### 5. Channels (`channels.py`)

Message delivery system that formats and routes agent outputs:

- Supports Slack (with Block Kit), Email (SMTP), and API webhooks
- Automatic formatting based on channel type
- Instructions-based customization

### 6. Configuration (`config.py`)

Environment-based configuration management:

```python
from broadie.config import settings

# Database configuration
settings.DATABASE_URL
settings.DATABASE_POOL_SIZE

# Model settings
settings.EMBEDDING_MODEL
settings.LLM_MODEL

# Channel credentials
settings.SLACK_BOT_TOKEN
settings.SMTP_HOST
```

### 7. Server (`server/`)

FastAPI-based web server with:

- **`app.py`**: Core FastAPI application setup
- **`playground.py`**: Interactive chat interface
- **`static/`**: Web UI assets (HTML, CSS, JS)

### 8. Agent-to-Agent (A2A) Communication (`a2a/`)

Inter-agent communication system:

- **`register.py`**: Agent registry management
- **`routes.py`**: A2A API endpoints
- **`utils.py`**: A2A utility functions

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Poetry or pip for dependency management
- Environment variables configured (see `.env` example)

### Google Cloud Authentication

This project requires access to Google Cloud Vertex AI. You must set up
[Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/provide-credentials-adc).

1. In your Google Cloud project, create or select a **service account** with
   permissions to use Vertex AI (e.g. `roles/aiplatform.user`).

2. Generate a JSON key for that service account and download it to your machine:
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=YOUR_SA_NAME@YOUR_PROJECT.iam.gserviceaccount.com
   ```

3. Export the path to this JSON file so that libraries inside the container
   or locally can find it:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
   ```

4. (Optional) Set your GCP project and region explicitly:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   gcloud config set ai/region us-central1
   ```

5. Verify that authentication works:
   ```bash
   gcloud auth application-default print-access-token
   ```

Once this is done, you can run:
```bash
broadie serve agents/phishing.py:agent
```
and the Vertex AI integration will have the required credentials.

### Installation

```bash
# Clone the repository
git clone https://github.com/broadinstitute/broadie.git
cd broadie

# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your configuration
```

### Basic Usage

#### 1. Create a Simple Agent

```python
from broadie import create_agent

# Create a basic agent
agent = create_agent(
    name="assistant",
    instruction="You are a helpful assistant"
)

# Run the agent
def main():
    import asyncio
    response = asyncio.run(agent.run("Hello, how can you help me?"))
    print(response)
```

#### 2. Agent with Tools and Channels

```python
from broadie import create_agent, tool

@tool("calculator")
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

agent = create_agent(
    name="math_assistant",
    instruction="You are a math tutor",
    tools=[add_numbers],
    channels=[{
        "type": "slack",
        "target": "#math-help",
        "instructions": "Format responses as educational content"
    }]
)
```

#### 3. Agent with Sub-Agents

```python
from broadie import create_agent, create_sub_agent

# Create specialized sub-agents
search_agent = create_sub_agent(
    name="searcher",
    prompt="You specialize in finding information",
    tools=["web_search"]
)

calculator_agent = create_sub_agent(
    name="calculator",
    prompt="You specialize in mathematical calculations",
    tools=["calculator"]
)

# Main coordinator agent
main_agent = create_agent(
    name="coordinator",
    instruction="Coordinate between search and calculation tasks",
    subagents=[search_agent, calculator_agent]
)
```

### CLI Usage

```bash
# Serve an agent
broadie serve examples/simple.py:simple_agent --host 0.0.0.0 --port 8000

# Interactive chat mode
broadie run examples/simple.py:simple_agent

# Check version
broadie version
```

### Web Interface

Access the playground at: `http://localhost:8000/{agent_id}/playground`

### Running Agents Programmatically

You can run agents directly in your Python code using the async pattern:

```python
from broadie import create_agent, create_sub_agent
phish_guardian = create_agent(
    name="phish_guardian",
    instruction="Detect and respond to phishing attempts",
)
if __name__ == "__main__":
    import asyncio

    async def main():
        email_message = (
            "Hello user, please reset your password here: http://bad-link.com"
        )
        result = await phish_guardian.run(email_message)
        print(result)

    asyncio.run(main())
```

This pattern is used throughout the examples and allows you to:
- Run agents asynchronously for better performance
- Handle multiple concurrent requests
- Integrate with existing async codebases
- Test agents interactively

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/broadie/test_agents.py

# Run with coverage
pytest --cov=src/broadie

# Run linting and formatting
black . && isort . && ruff check --fix
```

### Test Structure

```
tests/
├── broadie/
│   ├── test_agents.py     # Agent functionality tests
│   ├── test_factory.py    # Factory function tests
│   ├── test_schemas.py    # Schema validation tests
│   ├── test_config.py     # Configuration tests
│   ├── test_channels.py   # Channel agent tests
│   ├── test_mixins.py     # Persistence mixin tests
│   ├── test_prompts.py    # Prompt template tests
│   ├── test_cli.py        # CLI command tests
│   └── tools/
│       ├── test_memory.py    # Memory tool tests
│       ├── test_channels.py  # Channel tool tests
│       └── test_tasks.py     # Task tool tests
└── conftest.py           # Shared test fixtures
```

### Writing Tests

We use pytest with extensive mocking to avoid external API calls:

```python
import pytest
from unittest.mock import AsyncMock, patch
from broadie import create_agent

@pytest.mark.asyncio
async def test_agent_response():
    with patch("broadie.agents.create_react_agent") as mock_create:
        mock_runtime = AsyncMock()
        mock_runtime.ainvoke.return_value = {"messages": [Mock(content="Hello!")]}
        mock_create.return_value = mock_runtime

        agent = create_agent(name="test", instruction="Be helpful")
        response = await agent.run("Hi there")

        assert "Hello!" in str(response)
```

## 🔧 Development Guidelines

### Code Style

We follow Python best practices with automated tooling:

- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast Python linting
- **Type hints**: Required for all public APIs

### Architecture Principles

1. **Separation of Concerns**: Each module has a clear, single responsibility
2. **Dependency Injection**: Use configuration and factory patterns
3. **Type Safety**: Leverage Pydantic schemas for data validation
4. **Testability**: Design for easy mocking and unit testing
5. **Extensibility**: Plugin-like architecture for tools and channels

### Adding New Components

#### Adding a New Tool

A `ToolResponse` class was created with comprehensive fields and utility methods. All inbuilt tools were updated to use this class and proper input schemas. `ToolResponse` and `ToolStatus` were also added to the main `__all__` export list.

```python
# In tools/my_tool.py
import time
# from langchain_core.tools import tool
from pydantic import BaseModel, Field
from broadie.tools.channels import ToolResponse, ToolStatus, tool

class MyToolInput(BaseModel):
    query: str = Field(description="The search query")
    limit: int = Field(default=10, description="Maximum number of results")

@tool("my_tool", args_schema=MyToolInput, description="Search for information")
async def my_tool(query: str, limit: int = 10) -> ToolResponse:
    """Description of what this tool does."""
    start_time = time.time()

    try:
        # Your tool implementation here
        results = perform_search(query, limit)

        return ToolResponse.success(
            message=f"Successfully found {len(results)} results for '{query}'",
            data={"results": results, "query": query, "count": len(results)},
            meta={
                "query": query,
                "limit": limit,
                "actual_count": len(results)
            },
            tool_name="my_tool",
            execution_time_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        return ToolResponse.fail(
            message=f"Failed to search for '{query}'",
            error_details={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "query": query
            },
            meta={"query": query, "limit": limit},
            tool_name="my_tool",
            execution_time_ms=(time.time() - start_time) * 1000
        )

# Usage in your code
from broadie import ToolResponse, ToolStatus

# The ToolResponse class provides comprehensive response handling:
# - status: ToolStatus enum (SUCCESS, ERROR, WARNING, etc.)
# - message: Human-readable description
# - data: Tool-specific response data
# - error: Error details if operation failed
# - meta: Additional metadata
# - timestamp: When response was created
# - tool_name: Name of the tool
# - execution_time_ms: Execution time in milliseconds
```

#### Adding a New Channel Type

```python
# In tools/channels.py
from broadie.tools.channels import ToolResponse, tool
@tool("send_my_channel_tool")
async def send_my_channel_tool(message: str, target: str) -> ToolResponse:
    """Send message via my custom channel."""
    # Implementation here
    return ToolResponse.success(message="sent", meta={"target": target})
```

#### Extending Configuration

```python
# In config.py
class Settings:
    def __init__(self):
        # Add new configuration option
        self.MY_NEW_SETTING: str = os.getenv("MY_NEW_SETTING", "default_value")
```

## 📋 Contributing Workflow

### 1. Setting Up Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/broadie.git
cd broadie

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install black isort pytest ruff
```

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Format and lint code
black . && isort . && ruff check --fix

# Run tests
pytest

# Commit changes
git commit -m "feat: describe your changes"
```

### 3. Submitting Changes

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Include description of changes and any breaking changes
```

### Pull Request Guidelines

- **Clear Description**: Explain what your PR does and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update relevant documentation
- **Backwards Compatibility**: Avoid breaking changes when possible
- **Small, Focused Changes**: Keep PRs focused on a single concern

## 🏗️ Key Extension Points

### Custom Agent Types

Extend `BaseAgent` for specialized agent behavior:

```python
from broadie.agents import BaseAgent

class CustomAgent(BaseAgent):
    def agent_tools(self):
        return ["custom_tool_1", "custom_tool_2"]

    async def custom_method(self):
        # Custom agent behavior
        pass
```

### Custom Schemas

Define new data models:

```python
from pydantic import BaseModel, Field

class CustomSchema(BaseModel):
    field1: str = Field(description="Description")
    field2: int = Field(default=42)
```

### Middleware and Hooks

Extend server functionality:

```python
# In server/app.py
@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    # Custom middleware logic
    response = await call_next(request)
    return response
```

## 🔍 Debugging and Troubleshooting

### Common Issues

1. **Agent not responding**: Check LangSmith tracing and model configuration
2. **Tool errors**: Verify tool schemas and input validation
3. **Channel delivery failures**: Check credentials and network connectivity
4. **Configuration issues**: Verify environment variables and `.env` file

### Debugging Tools

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use LangSmith for tracing
settings.LANGCHAIN_TRACING_V2 = True
settings.LANGCHAIN_API_KEY = "your-key"

# Debug agent runtime
agent.runtime.debug = True
```

## 📚 Additional Resources

- **LangChain Documentation**: https://docs.langchain.com/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Pytest Documentation**: https://docs.pytest.org/

## 🤝 Community

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join conversations in GitHub Discussions
- **Email**: Contact the team at broadie@broadinstitute.org

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Happy Contributing!** 🚀

The broadie framework is designed to be extensible and developer-friendly. Whether you're fixing bugs, adding features, or improving documentation, your contributions help make AI agent development more accessible and reliable.
