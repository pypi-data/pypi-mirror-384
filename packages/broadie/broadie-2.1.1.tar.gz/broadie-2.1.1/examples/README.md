# Broadie Examples

This directory contains example agents demonstrating various Broadie features.

## Running Examples

All examples follow the same pattern and can be run using:

```bash
broadie chat examples/{filename}.py:agent
```

## Available Examples

### 1. Simple Agent (`simple.py`)
**Run:** `broadie chat examples/simple.py:agent`

Basic agent with 3 tools and no approval workflows.
- **Tools:** Weather lookup, news search, calculator
- **Demonstrates:** Basic tool usage, structured output
- **Use Case:** General-purpose assistant for simple queries

### 2. Standard Agent (`standard.py`)
**Run:** `broadie chat examples/standard.py:agent`

Agent with 2 subagents for delegation, no approval workflows.
- **Main Agent:** Threat intelligence analyst
- **Subagents:** IPEnricher, DomainEnricher
- **Tools:** IP lookup, domain lookup, URL scanning
- **Demonstrates:** Subagent delegation, structured output, tool organization
- **Use Case:** Security indicator analysis

### 3. Advanced Agent (`advanced.py`)
**Run:** `broadie chat examples/advanced.py:agent`

Complex agent with multiple subagents and coordinated analysis.
- **Main Agent:** Senior threat intelligence analyst
- **Subagents:** NetworkAnalyzer, MalwareAnalyzer
- **Tools:** IP lookup, domain lookup, file hash lookup
- **Demonstrates:** Multiple subagents, coordinated analysis, nested structured outputs
- **Use Case:** Comprehensive threat intelligence analysis

### 4. Simple with Approval (`simple_with_approval.py`)
**Run:** `broadie chat examples/simple_with_approval.py:agent`

Basic agent with 3 tools where 1 requires human approval.
- **Main Agent:** File manager
- **Tools:** Read file, list files, delete file (requires approval)
- **Demonstrates:** Approval workflows, CLI/API interrupt handling
- **Use Case:** File management with safety controls

### 5. Advanced with Approval (`advanced_with_approval.py`)
**Run:** `broadie chat examples/advanced_with_approval.py:agent`

Complex agent with subagents where both main agent and subagents have tools requiring approval.
- **Main Agent:** Security incident response coordinator
- **Subagents:** NetworkResponder, EndpointResponder
- **Tools with Approval:**
  - Main: Block indicator
  - Network: Isolate host
  - Endpoint: Terminate process
- **Demonstrates:** Multi-level approval workflows, subagent delegation with approvals
- **Use Case:** Security incident response with human oversight

## Code Pattern

All examples use the same simplified pattern:

```python
from broadie import create_agent, tool, ToolResponse, ToolStatus

@tool(name="example_tool", parse_docstring=True)
def example_tool(param: str) -> ToolResponse:
    """Tool description."""
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message="Operation completed",
        data={"result": "value"},
    )

agent = create_agent(
    name="ExampleAgent",
    instruction="Agent instructions...",
    tools=[example_tool],
)
```

## Tool Response Pattern

All tools return `ToolResponse` with `ToolStatus.SUCCESS` or `ToolStatus.ERROR`:

```python
# Success
return ToolResponse(
    status=ToolStatus.SUCCESS,
    message="Operation completed successfully",
    data={"key": "value"},
)

# Error
return ToolResponse(
    status=ToolStatus.ERROR,
    message="Operation failed: reason",
    data={"error": "details"},
)
```

## Approval Pattern

Tools requiring approval use the `approval_required` parameter:

```python
@tool(
    name="dangerous_operation",
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Perform dangerous operation on {target}?",
    risk_level="high",  # or "critical"
)
def dangerous_operation(target: str) -> ToolResponse:
    """Perform operation requiring approval."""
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Operation performed on {target}",
        data={"target": target, "completed": True},
    )
```

## Next Steps

1. Try each example with different queries
2. Modify examples to add your own tools
3. Experiment with subagent coordination
4. Test approval workflows in different scenarios
