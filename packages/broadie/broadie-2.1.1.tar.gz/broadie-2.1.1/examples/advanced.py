"""
Advanced Agent Example

Complex agent with multiple subagents and coordinated threat analysis.
Demonstrates: Multiple subagents, coordinated analysis, nested structured outputs

Run with: broadie chat examples/advanced.py:agent
"""

from enum import Enum

from pydantic import BaseModel, Field

from broadie import ToolResponse, ToolStatus, create_agent, create_sub_agent, tool


# Tools
@tool(name="lookup_ip", parse_docstring=True)
def lookup_ip(ip: str) -> ToolResponse:
    """Look up IP reputation in a threat intel database.

    Args:
        ip: IP address to look up

    Returns:
        IP reputation information
    """
    reputation = "malicious" if ip.startswith("192.") else "clean"
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"IP {ip} reputation lookup completed",
        data={"ip": ip, "reputation": reputation},
        meta={"source": "threat_intel_db", "lookup_type": "ip"},
    )


@tool(name="lookup_domain", parse_docstring=True)
def lookup_domain(domain: str) -> ToolResponse:
    """Check domain reputation in DNS and threat feeds.

    Args:
        domain: Domain name to check

    Returns:
        Domain reputation information
    """
    category = "phishing" if "phish" in domain else "benign"
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Domain {domain} reputation lookup completed",
        data={"domain": domain, "category": category},
        meta={"source": "dns_threat_feeds", "lookup_type": "domain"},
    )


@tool(name="lookup_hash", parse_docstring=True)
def lookup_hash(file_hash: str) -> ToolResponse:
    """Look up file hash in malware databases.

    Args:
        file_hash: File hash to look up (MD5, SHA1, SHA256)

    Returns:
        File hash reputation information
    """
    is_malicious = len(file_hash) > 20
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Hash {file_hash} lookup completed",
        data={"hash": file_hash, "malicious": is_malicious, "detections": 45 if is_malicious else 0},
        meta={"source": "malware_db", "lookup_type": "hash"},
    )


# Output Schemas
class Verdict(str, Enum):
    malicious = "malicious"
    suspicious = "suspicious"
    benign = "benign"
    unknown = "unknown"


class EnrichmentResult(BaseModel):
    indicator: str = Field(description="The security indicator analyzed")
    type: str = Field(description="Type of indicator (ip, domain, url, hash)")
    verdict: Verdict = Field(description="Security verdict")
    confidence: float = Field(description="Confidence score (0-1)")


class ThreatIntelOutput(BaseModel):
    summary: str = Field(description="Human-readable summary of the threat analysis")
    overall_risk: str = Field(description="Overall risk level (low, medium, high, critical)")
    enrichments: list[EnrichmentResult] = Field(description="List of enriched indicators with verdicts")
    recommendations: list[str] = Field(description="Security recommendations")


# Create subagents
network_analyzer = create_sub_agent(
    name="NetworkAnalyzer",
    prompt="Analyze IPs and domains for network-based threats.",
    description="Specializes in analyzing network indicators (IPs, domains)",
    tools=[lookup_ip, lookup_domain],
    capabilities=["network_analysis", "threat_intel"],
    tags=["security", "network"],
)

malware_analyzer = create_sub_agent(
    name="MalwareAnalyzer",
    prompt="Analyze file hashes and identify malware.",
    description="Specializes in malware detection and file hash analysis",
    tools=[lookup_hash],
    capabilities=["malware_analysis", "hash_lookup"],
    tags=["security", "malware"],
)

# Create agent directly - works for both library and CLI usage
agent = create_agent(
    name="ThreatIntelAgent",
    instruction=(
        "You are a senior threat intelligence analyst. "
        "Coordinate with NetworkAnalyzer for IP/domain analysis and MalwareAnalyzer for file analysis. "
        "Analyze all indicators comprehensively and provide actionable security recommendations. "
        "Assess overall risk and prioritize threats."
    ),
    output_schema=ThreatIntelOutput,
    tools=[lookup_ip, lookup_domain, lookup_hash],
    subagents=[network_analyzer, malware_analyzer],
)
