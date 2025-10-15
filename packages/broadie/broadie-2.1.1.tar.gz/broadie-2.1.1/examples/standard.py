"""
Standard Agent Example

Agent with subagents for delegation, no approval workflows.
Demonstrates: Subagent delegation, structured output, tool organization

Run with: broadie chat examples/standard.py:agent
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from broadie import ToolResponse, ToolStatus, create_agent, create_sub_agent, tool


# Tools
@tool(name="lookup_ip", parse_docstring=True)
def lookup_ip(ip: str) -> ToolResponse:
    """Look up IP reputation in threat intelligence database.

    Args:
        ip: IP address to look up

    Returns:
        IP reputation and threat information
    """
    reputation = "malicious" if ip.startswith("192.") else "clean"
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"IP {ip} reputation lookup completed",
        data={"ip": ip, "reputation": reputation, "threat_score": 85 if reputation == "malicious" else 10},
    )


@tool(name="lookup_domain", parse_docstring=True)
def lookup_domain(domain: str) -> ToolResponse:
    """Check domain reputation in DNS and threat feeds.

    Args:
        domain: Domain name to check

    Returns:
        Domain reputation and category information
    """
    category = "phishing" if "phish" in domain else "benign"
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Domain {domain} reputation lookup completed",
        data={"domain": domain, "category": category, "malicious": category != "benign"},
    )


@tool(name="scan_url", parse_docstring=True)
def scan_url(url: str) -> ToolResponse:
    """Scan a URL for security threats.

    Args:
        url: URL to scan

    Returns:
        URL scan results and threat assessment
    """
    is_safe = "safe-site" in url
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"URL {url} scanned",
        data={"url": url, "safe": is_safe, "threats": [] if is_safe else ["malware", "phishing"]},
    )


# Output Schemas
class EnrichmentResult(BaseModel):
    indicator: str = Field(description="The indicator that was analyzed (IP, domain, URL)")
    indicator_type: str = Field(description="Type of indicator")
    verdict: str = Field(description="Security verdict (clean, suspicious, malicious)")
    details: dict = Field(description="Additional enrichment details")


class ThreatIntelOutput(BaseModel):
    summary: str = Field(description="Human-readable summary of threat analysis")
    indicators_analyzed: int = Field(description="Number of indicators analyzed")
    enrichments: list[EnrichmentResult] = Field(description="List of enriched indicators")


# Create subagents
ip_enricher = create_sub_agent(
    name="IPEnricher",
    prompt="You analyze IP addresses and provide threat intelligence context.",
    description="Enriches IP addresses with threat intelligence data",
    tools=[lookup_ip],
    capabilities=["ip_analysis", "threat_intel"],
    tags=["security", "networking"],
)

domain_enricher = create_sub_agent(
    name="DomainEnricher",
    prompt="You analyze domains and URLs for security threats.",
    description="Enriches domains and URLs with security information",
    tools=[lookup_domain, scan_url],
    capabilities=["domain_analysis", "url_scanning"],
    tags=["security", "web"],
)

# Create agent directly - works for both library and CLI usage
agent = create_agent(
    name="threat_Intel_Agent",
    instruction=(
        "You are a threat intelligence analyst. "
        "Analyze security indicators (IPs, domains, URLs) from user input. "
        "Use IPEnricher for IP addresses and DomainEnricher for domains/URLs. "
        "Provide comprehensive security assessments."
    ),
    tools=[lookup_ip, lookup_domain, scan_url],
    subagents=[ip_enricher, domain_enricher],
    output_schema=ThreatIntelOutput,
)
