"""
Mock Agent Example - Complete Workflow Demo

Demonstrates the simplified usage pattern:
1. Import from broadie
2. Create agent with create_agent() - returns immediately
3. Use agent.run("message") - handles async internally
4. Subagents with approval-required tools

Run with:
    broadie chat examples/mock_agent.py:agent

Or programmatically:
    python examples/mock_agent.py
"""

from pydantic import BaseModel, Field

from broadie import ToolResponse, ToolStatus, create_agent, create_sub_agent, tool

# =============================================================================
# TOOLS - Main Agent
# =============================================================================


@tool(name="analyze_system", parse_docstring=True)
def analyze_system(system_name: str) -> ToolResponse:
    """Analyze a system's health and status.

    Args:
        system_name: Name of the system to analyze

    Returns:
        System analysis results
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"System {system_name} analyzed successfully",
        data={
            "system": system_name,
            "status": "healthy",
            "cpu_usage": 45,
            "memory_usage": 62,
            "disk_usage": 78,
        },
    )


@tool(
    name="restart_system",
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Restart system {system_name}? This will cause downtime!",
    risk_level="high",
)
def restart_system(system_name: str) -> ToolResponse:
    """Restart a system - REQUIRES APPROVAL!

    This is a critical operation that requires human approval.

    Args:
        system_name: Name of the system to restart

    Returns:
        Restart operation result
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"System {system_name} restarted successfully",
        data={"system": system_name, "restarted": True, "downtime_seconds": 30},
    )


# =============================================================================
# TOOLS - Database Subagent
# =============================================================================


@tool(name="query_database", parse_docstring=True)
def query_database(query: str) -> ToolResponse:
    """Execute a read-only database query.

    Args:
        query: SQL query to execute (SELECT only)

    Returns:
        Query results
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Query executed: {query[:50]}...",
        data={
            "query": query,
            "rows_returned": 42,
            "execution_time_ms": 125,
            "results": [{"id": 1, "name": "Example Row"}],
        },
    )


@tool(
    name="backup_database",
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Backup database {database_name}? This may impact performance!",
    risk_level="medium",
)
def backup_database(database_name: str) -> ToolResponse:
    """Backup a database - REQUIRES APPROVAL!

    This operation may impact database performance.

    Args:
        database_name: Name of the database to backup

    Returns:
        Backup operation result
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Database {database_name} backed up successfully",
        data={
            "database": database_name,
            "backup_file": f"{database_name}_backup_20251009.sql",
            "size_mb": 1024,
            "duration_seconds": 45,
        },
    )


# =============================================================================
# TOOLS - Network Subagent
# =============================================================================


@tool(name="check_connectivity", parse_docstring=True)
def check_connectivity(host: str) -> ToolResponse:
    """Check network connectivity to a host.

    Args:
        host: Hostname or IP address to check

    Returns:
        Connectivity check results
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Connectivity to {host} checked",
        data={
            "host": host,
            "reachable": True,
            "latency_ms": 23,
            "packet_loss": 0,
        },
    )


@tool(
    name="block_ip",
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Block IP {ip_address} on firewall? This is irreversible!",
    risk_level="critical",
)
def block_ip(ip_address: str, reason: str = "Security threat") -> ToolResponse:
    """Block an IP address on the firewall - REQUIRES APPROVAL!

    This is a critical security operation that requires human approval.

    Args:
        ip_address: IP address to block
        reason: Reason for blocking

    Returns:
        Block operation result
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"IP {ip_address} blocked on firewall",
        data={
            "ip": ip_address,
            "blocked": True,
            "reason": reason,
            "rule_id": "FW-BLOCK-12345",
        },
    )


# =============================================================================
# OUTPUT SCHEMAS
# =============================================================================


class OperationResult(BaseModel):
    """Result of an individual operation."""

    operation: str = Field(description="Operation that was performed")
    success: bool = Field(description="Whether the operation succeeded")
    details: str = Field(description="Details about the operation")
    approval_required: bool = Field(description="Whether approval was required")


class SystemManagementOutput(BaseModel):
    """Output schema for system management operations."""

    summary: str = Field(description="Human-readable summary of what was done")
    operations_performed: list[OperationResult] = Field(description="List of operations performed")
    recommendations: list[str] = Field(description="Additional recommendations")
    risk_level: str = Field(description="Overall risk level of operations (low, medium, high, critical)")


# =============================================================================
# AGENT DEFINITION - Simple API!
# =============================================================================

# Create subagents (synchronous - they're just schemas)
database_admin = create_sub_agent(
    name="DatabaseAdmin",
    prompt="You manage database operations including queries and backups.",
    description="Handles database administration tasks",
    tools=[query_database, backup_database],
    capabilities=["database_query", "database_backup"],
    tags=["database", "admin"],
)

network_admin = create_sub_agent(
    name="NetworkAdmin",
    prompt="You manage network operations including connectivity checks and firewall rules.",
    description="Handles network administration tasks",
    tools=[check_connectivity, block_ip],
    capabilities=["network_check", "firewall_management"],
    tags=["network", "security"],
)


# Create agent - returns immediately, no await needed
# This is now a factory function to avoid event loop issues in tests
def create_mock_agent():
    """Factory function to create a fresh agent instance."""
    return create_agent(
        name="SystemManager",
        instruction=(
            "You are a system management agent. You coordinate system operations and delegate to specialized agents. "
            "Use DatabaseAdmin for database operations and NetworkAdmin for network operations. "
            "Always provide clear summaries and recommendations."
        ),
        tools=[analyze_system, restart_system],
        subagents=[database_admin, network_admin],
        output_schema=SystemManagementOutput,
    )


# Global agent instance for backward compatibility (chat/serve modes)
agent = create_mock_agent()
