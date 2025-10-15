"""
Advanced Agent with Approval Example

Complex agent with subagents where both main agent and subagents have tools requiring approval.
Demonstrates: Multi-level approval workflows, subagent delegation with approvals, complex workflows

Run with: broadie chat examples/advanced_with_approval.py:agent
"""

from pydantic import BaseModel, Field

from broadie import ToolResponse, ToolStatus, create_agent, create_sub_agent, tool


# Main Agent Tools
@tool(parse_docstring=True)
def analyze_threat(indicator: str) -> ToolResponse:
    """Analyze a security threat indicator.

    Args:
        indicator: Security indicator to analyze (IP, domain, hash)

    Returns:
        Threat analysis results
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Analyzed threat indicator: {indicator}",
        data={"indicator": indicator, "threat_level": "high", "confidence": 0.85},
    )


@tool(
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Block indicator {indicator} across all systems?",
    risk_level="high",
)
def block_indicator(indicator: str, reason: str = "Security threat") -> ToolResponse:
    """Block a threat indicator - REQUIRES APPROVAL!

    This will block the indicator across all security systems.

    Args:
        indicator: Threat indicator to block
        reason: Reason for blocking

    Returns:
        Block operation result
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Blocked indicator: {indicator}",
        data={"indicator": indicator, "blocked": True, "reason": reason},
    )


# Network SubAgent Tools
@tool(parse_docstring=True)
def scan_network(network_range: str) -> ToolResponse:
    """Scan a network range for active hosts.

    Args:
        network_range: Network range to scan (e.g., 192.168.1.0/24)

    Returns:
        List of active hosts found
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Scanned network: {network_range}",
        data={"network": range, "hosts_found": ["192.168.1.100", "192.168.1.101"]},
    )


@tool(
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Isolate host {host_ip} from network? This will disconnect it!",
    risk_level="critical",
)
def isolate_host(host_ip: str, reason: str = "Security incident") -> ToolResponse:
    """Isolate a host from the network - REQUIRES APPROVAL!

    This will immediately disconnect the host from the network.

    Args:
        host_ip: IP address of host to isolate
        reason: Reason for isolation

    Returns:
        Isolation operation result
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Isolated host: {host_ip}",
        data={"host_ip": host_ip, "isolated": True, "reason": reason},
    )


# Endpoint SubAgent Tools
@tool(parse_docstring=True)
def query_endpoint(endpoint_id: str, query: str) -> ToolResponse:
    """Query an endpoint for information.

    Args:
        endpoint_id: Endpoint identifier
        query: Query to run on the endpoint

    Returns:
        Query results from the endpoint
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Queried endpoint: {endpoint_id}",
        data={"endpoint_id": endpoint_id, "query": query, "results": ["process1.exe", "process2.exe"]},
    )


@tool(
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Terminate process {process_name} on endpoint {endpoint_id}?",
    risk_level="high",
)
def terminate_process(endpoint_id: str, process_name: str) -> ToolResponse:
    """Terminate a process on an endpoint - REQUIRES APPROVAL!

    This will forcefully kill the process.

    Args:
        endpoint_id: Endpoint identifier
        process_name: Name of process to terminate

    Returns:
        Process termination result
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Terminated process {process_name} on {endpoint_id}",
        data={"endpoint_id": endpoint_id, "process_name": process_name, "terminated": True},
    )


# Output Schemas
class ActionTaken(BaseModel):
    action: str = Field(description="Action that was taken")
    target: str = Field(description="Target of the action")
    required_approval: bool = Field(description="Whether approval was required")
    status: str = Field(description="Status of the action")


class SecurityResponse(BaseModel):
    summary: str = Field(description="Summary of security response")
    threat_level: str = Field(description="Overall threat level")
    actions_taken: list[ActionTaken] = Field(description="List of actions taken")
    recommendations: list[str] = Field(description="Additional recommendations")


# Create subagents
network_responder = create_sub_agent(
    name="NetworkResponder",
    prompt="Handle network-level security responses and isolation.",
    description="Manages network security responses including scanning and host isolation",
    tools=[scan_network, isolate_host],
    capabilities=["network_scan", "host_isolation"],
    tags=["security", "network", "incident_response"],
)

endpoint_responder = create_sub_agent(
    name="EndpointResponder",
    prompt="Handle endpoint security responses and process termination.",
    description="Manages endpoint security including process analysis and termination",
    tools=[query_endpoint, terminate_process],
    capabilities=["endpoint_query", "process_termination"],
    tags=["security", "endpoint", "incident_response"],
)

# Create agent directly - works for both library and CLI usage
agent = create_agent(
    name="SecurityResponseAgent",
    instruction=(
        "You are a security incident response coordinator. "
        "Analyze threats, coordinate with NetworkResponder and EndpointResponder subagents. "
        "For critical actions (blocking indicators, isolating hosts, terminating processes), "
        "explain the action clearly and wait for approval. "
        "Provide comprehensive security response recommendations."
    ),
    tools=[analyze_threat, block_indicator],
    subagents=[network_responder, endpoint_responder],
    output_schema=SecurityResponse,
)
