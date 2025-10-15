# 🤖 Broadie

**Production-grade AI Agent Framework with Swarm Architecture**

Build, deploy, and scale AI agents with built-in persistence, approval workflows, and multi-agent coordination.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start

### Installation

```bash
pip install broadie
```

### Your First Agent in 30 Seconds

```python
from broadie import create_agent, tool

@tool(parse_docstring=True)
def get_weather(city: str) -> dict:
    """Get weather for a city.

    Args:
        city: Name of the city
    """
    return {"city": city, "temperature": 72, "condition": "sunny"}

agent = create_agent(
    name="WeatherBot",
    instruction="You are a helpful weather assistant.",
    tools=[get_weather]
)
```

Run it:

```bash
# Interactive chat
broadie chat myagent.py:agent

# Or as an API server
broadie serve myagent.py:agent --port 8000
```

---

## 📚 Table of Contents

- [Building Your First Agent](#building-your-first-agent)
- [Agent Coordination with SubAgents](#agent-coordination-with-subagents)
- [Structured Outputs](#structured-outputs)
- [Creating Tools](#creating-tools)
- [Approval Workflows](#approval-workflows)
- [Deployment](#deployment)
- [Examples](#examples)
- [Documentation](#documentation)

---

## 🎯 Building Your First Agent

### Simple Agent

Create an agent with custom tools:

```python
from broadie import create_agent, tool

# Define tools
@tool(parse_docstring=True)
def calculate(expression: str) -> dict:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate (e.g., "2 + 2")

    Returns:
        Calculation result
    """
    result = eval(expression)
    return {"expression": expression, "result": result}

@tool(parse_docstring=True)
def get_time() -> dict:
    """Get the current time."""
    from datetime import datetime
    return {"time": datetime.now().isoformat()}

# Create agent
agent = create_agent(
    name="MathBot",
    instruction="You are a helpful math assistant. Use tools to perform calculations.",
    tools=[calculate, get_time]
)
```

### Run Your Agent

#### CLI Chat Mode

```bash
broadie chat myagent.py:agent
```

```
💬 Chatting with agent 'mathbot' (Ctrl+C to quit)
You: What is 15 * 23?
mathbot> Let me calculate that for you. 15 × 23 = 345
You: What time is it?
mathbot> The current time is 2025-10-07T14:30:00
```

#### API Server Mode

```bash
broadie serve myagent.py:agent --port 8000
```

```bash
# Call your agent via API
curl -X POST http://localhost:8000/agent/mathbot/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 100 divided by 4?"}'
```

**[See full example →](examples/simple.py)**

---

## 🔄 Agent Coordination with SubAgents

Build multi-agent systems where agents delegate tasks to specialized sub-agents:

```python
from broadie import create_agent, create_sub_agent, tool

# SubAgent 1: Data Analyzer
@tool(parse_docstring=True)
def analyze_data(data: str) -> dict:
    """Analyze data and return insights."""
    return {"analysis": f"Analyzed: {data}", "insights": ["Pattern A", "Trend B"]}

analyzer = create_sub_agent(
    name="DataAnalyzer",
    prompt="You analyze data and provide insights.",
    tools=[analyze_data],
    capabilities=["data_analysis", "statistics"]
)

# SubAgent 2: Report Generator
@tool(parse_docstring=True)
def generate_report(title: str, content: str) -> dict:
    """Generate a formatted report."""
    return {"title": title, "report": f"# {title}\n\n{content}"}

reporter = create_sub_agent(
    name="ReportGenerator",
    prompt="You create well-formatted reports.",
    tools=[generate_report],
    capabilities=["report_generation", "formatting"]
)

# Main Agent: Coordinates sub-agents
coordinator = create_agent(
    name="ResearchCoordinator",
    instruction=(
        "You coordinate research tasks. "
        "Use DataAnalyzer for analysis and ReportGenerator for reports. "
        "Delegate appropriately based on the task."
    ),
    subagents=[analyzer, reporter]
)
```

### How It Works

1. User sends request to main agent
2. Main agent determines which sub-agent(s) to use
3. Sub-agents execute their specialized tasks
4. Main agent synthesizes results

**[See full example →](examples/advanced.py)**

---

## 📊 Structured Outputs

Get structured, validated responses using Pydantic schemas:

### Agent-Level Structured Output

```python
from pydantic import BaseModel, Field
from broadie import create_agent, tool

# Define output schema
class WeatherReport(BaseModel):
    city: str = Field(description="City name")
    temperature: int = Field(description="Temperature in Fahrenheit")
    conditions: list[str] = Field(description="Weather conditions")
    recommendation: str = Field(description="Clothing recommendation")

@tool(parse_docstring=True)
def get_weather(city: str) -> dict:
    """Get weather data for a city."""
    return {
        "city": city,
        "temp": 72,
        "conditions": ["sunny", "clear"]
    }

# Agent returns structured output
agent = create_agent(
    name="WeatherAgent",
    instruction="Provide weather info and clothing recommendations.",
    tools=[get_weather],
    output_schema=WeatherReport  # ← Structured output
)

# Response is a validated Pydantic model
result = await agent.run("What's the weather in Boston?")
print(result.city)           # "Boston"
print(result.temperature)    # 72
print(result.conditions)     # ["sunny", "clear"]
print(result.recommendation) # "Light jacket recommended"
```

### Tool-Level Structured Output

```python
from broadie import ToolResponse, ToolStatus, tool

@tool(parse_docstring=True)
def search_database(query: str) -> ToolResponse:
    """Search database and return structured results.

    Args:
        query: Search query
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message="Search completed",
        data={
            "results": ["result1", "result2"],
            "count": 2
        },
        meta={"search_time_ms": 45}
    )
```

**[See full example →](examples/standard.py)**

---

## 🔧 Creating Tools

Tools give your agents capabilities. Broadie uses a decorator-based approach:

### Basic Tool

```python
from broadie import tool

@tool(parse_docstring=True)
def search_web(query: str) -> dict:
    """Search the web for information.

    Args:
        query: Search query

    Returns:
        Search results
    """
    # Your search logic here
    return {"query": query, "results": [...]}
```

### Tool Parameters

```python
@tool(
    parse_docstring=True,           # Parse docstring for descriptions
    return_direct=False,             # Continue agent loop after tool
    infer_schema=True,               # Auto-generate schema from signature
    response_format="content"        # or "content_and_artifact"
)
def my_tool(arg: str) -> dict:
    """Tool description."""
    return {"result": arg}
```

### Tool Best Practices

✅ **DO:**
- Use clear, descriptive names
- Document parameters with Google-style docstrings
- Return structured data (dicts, ToolResponse)
- Handle errors gracefully

❌ **DON'T:**
- Use generic names like "tool1", "helper"
- Leave parameters undocumented
- Return raw strings without context
- Let exceptions bubble up unhandled

**[See tool examples →](examples/simple.py)**

---

## ✅ Approval Workflows

Add human-in-the-loop approval for sensitive operations:

### Tool with Approval

```python
from broadie import tool

@tool(
    parse_docstring=True,
    approval_required=True,                                    # ← Enable approval
    approval_message="⚠️ Delete file {filename}? Cannot be undone!",  # ← Custom message
    risk_level="high"                                          # ← Risk classification
)
def delete_file(filename: str) -> dict:
    """Delete a file - REQUIRES APPROVAL!

    Args:
        filename: Name of file to delete
    """
    import os
    os.remove(filename)
    return {"status": "deleted", "filename": filename}

agent = create_agent(
    name="FileManager",
    instruction="Help manage files. Always use tools for file operations.",
    tools=[delete_file]
)
```

### CLI Approval Flow

When a tool requires approval, execution pauses:

```bash
$ broadie chat myagent.py:agent

You: delete important.txt

============================================================
⚠️  APPROVAL REQUIRED
============================================================
Tool: delete_file
Risk Level: HIGH
Message: ⚠️ Delete file important.txt? Cannot be undone!

Arguments:
  filename: important.txt

============================================================

Decision: [a]pprove / [r]eject [r]: a
✅ Approving and resuming execution...

agent> File important.txt has been deleted successfully.
```

### API Approval Flow

#### 1. Request triggers interrupt

```bash
POST /agent/filemanager/invoke
{
  "message": "delete important.txt",
  "thread_id": "thread-123"
}
```

**Response:**
```json
{
  "agent": "filemanager",
  "response": {
    "status": "interrupted",
    "thread_id": "thread-123",
    "interrupt_data": {
      "type": "approval_request",
      "tool": "delete_file",
      "message": "⚠️ Delete file important.txt? Cannot be undone!",
      "risk_level": "high",
      "args": {"filename": "important.txt"}
    }
  },
  "next_actions": [
    "POST /agent/filemanager/approve",
    "POST /agent/filemanager/reject"
  ]
}
```

#### 2. Approve or reject

```bash
# Approve
POST /agent/filemanager/approve
{"thread_id": "thread-123"}

# OR Reject
POST /agent/filemanager/reject
{
  "thread_id": "thread-123",
  "feedback": "File still needed"
}
```

### Risk Levels

- **`low`**: Read-only operations, informational
- **`medium`**: Reversible changes (default)
- **`high`**: Destructive operations, data modifications
- **`critical`**: System-level changes, security-sensitive

### Advanced: Dynamic Approval Data

Provide additional context dynamically:

```python
def get_file_info(filename: str) -> dict:
    """Get file metadata for approval context."""
    import os
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        return {"file_size": size, "exists": True}
    return {"exists": False}

@tool(
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️ Delete {filename}? Size: {file_size} bytes",
    approval_data=get_file_info,  # ← Callable for dynamic data
    risk_level="high"
)
def delete_file(filename: str) -> dict:
    """Delete a file with size shown in approval."""
    import os
    os.remove(filename)
    return {"status": "deleted", "filename": filename}
```

**[See approval examples →](examples/simple_with_approval.py)**

---

## 🚀 Deployment

### Running as a Service

```bash
# Development
broadie serve myagent.py:agent --port 8000

# Production with multiple workers
broadie serve myagent.py:agent --port 8000 --workers 4 --host 0.0.0.0
```

### API Endpoints

Once running, your agent exposes:

- `GET /agent/{agent_id}/info` - Agent metadata
- `POST /agent/{agent_id}/invoke` - Send message to agent
- `POST /agent/{agent_id}/approve` - Approve pending operation
- `POST /agent/{agent_id}/reject` - Reject pending operation
- `GET /agent/{agent_id}/health` - Health check
- `GET /agent/{agent_id}/playground` - Interactive UI (if enabled)

### Environment Variables

```bash
# .env file
BROADIE_HOST=0.0.0.0
BROADIE_PORT=8000
BROADIE_DEBUG=false
BROADIE_CORS_ORIGINS=["https://yourdomain.com"]
BROADIE_PLAYGROUND_ENABLED=true

# Model configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["broadie", "serve", "myagent.py:agent", "--port", "8000", "--workers", "4"]
```

---

## 📖 Examples

### Simple Examples

- **[simple.py](examples/simple.py)** - Basic agent with tools
- **[simple_with_approval.py](examples/simple_with_approval.py)** - Agent with approval workflows

### Advanced Examples

- **[advanced.py](examples/advanced.py)** - Multi-agent with subagents
- **[advanced_with_approval.py](examples/advanced_with_approval.py)** - Complex security agent with approvals
- **[standard.py](examples/standard.py)** - Structured outputs with ToolResponse

### Running Examples

```bash
# Interactive chat
broadie chat examples/simple.py:agent

# API server
broadie serve examples/advanced.py:agent --port 8000

# Test programmatically
python examples/simple.py
```

---

## 📚 Documentation

### Core Concepts

- **[Agent Architecture](docs/README.md)** - How agents work
- **[Tool Decorator](docs/TOOL_DECORATOR_USAGE.md)** - Creating tools
- **[Approval Workflows](docs/INTERRUPT_APPROVAL_FLOW.md)** - Human-in-the-loop patterns
- **[Persistence](docs/PERSISTENCE.md)** - State management

### API Reference

- **[Agent API](docs/API_REFERENCE.md)** - Agent methods and properties
- **[CLI Commands](docs/CLI_REFERENCE.md)** - Command-line interface
- **[Configuration](docs/CONFIGURATION.md)** - Environment settings

### Guides

- **[Best Practices](docs/BEST_PRACTICES.md)** - Production patterns
- **[Testing Guide](docs/TESTING.md)** - Testing your agents
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment

---

## 🏗️ Architecture

Broadie is built on:

- **[LangChain](https://langchain.com/)** - Tool and chain abstractions
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** - Agent state management and workflows
- **[FastAPI](https://fastapi.tiangolo.com/)** - API server
- **[Pydantic](https://pydantic.dev/)** - Data validation

### Key Features

✅ **Swarm Architecture** - Multi-agent coordination with intelligent delegation
✅ **Built-in Persistence** - SQLite/PostgreSQL state management
✅ **Approval Workflows** - Human-in-the-loop for sensitive operations
✅ **Structured Outputs** - Type-safe responses with Pydantic
✅ **Production Ready** - Docker, health checks, monitoring
✅ **CLI & API** - Chat interface and REST API
✅ **Type Safe** - Full type hints throughout

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTION.md](docs/CONTRIBUTION.md) for guidelines.

```bash
# Clone repository
git clone https://github.com/broadinstitute/broadie.git
cd broadie

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
mypy src/
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with ❤️ by the Broad Institute team.

Powered by LangChain, LangGraph, and the open-source AI community.

---

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/broadinstitute/broadie/issues)
- **Discussions**: [GitHub Discussions](https://github.com/broadinstitute/broadie/discussions)

---

## 🎓 Learning Resources

### Tutorials

1. **[Build Your First Agent](docs/tutorials/first-agent.md)** - 5 minute quickstart
2. **[Multi-Agent Systems](docs/tutorials/multi-agent.md)** - Coordinate multiple agents
3. **[Production Deployment](docs/tutorials/production.md)** - Deploy to production

### Videos

- [Introduction to Broadie](https://example.com) (Coming soon)
- [Building Complex Agents](https://example.com) (Coming soon)

### Community

- Join our [Discord](https://discord.gg/broadie) (Coming soon)
- Follow us on [Twitter](https://twitter.com/broadie_ai) (Coming soon)

---

**Ready to build your first agent?** → [Quick Start](#-quick-start)

**Questions?** → [GitHub Discussions](https://github.com/broadinstitute/broadie/discussions)
