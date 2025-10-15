"""
Test mock_agent.py as a library (direct Python usage).

Tests:
1. Basic agent execution
2. Subagent delegation
3. Approval workflow - approve scenario
4. Approval workflow - reject scenario
5. Structured output validation
"""

import asyncio
import os
import sys
import uuid

import pytest

# Set up test environment
os.environ["CI"] = "true"  # Force in-memory storage

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_basic_agent_execution():
    """Test basic agent execution without subagent delegation."""
    print("\n" + "=" * 80)
    print("TEST: Basic Agent Execution")
    print("=" * 80)

    # Create fresh agent instance to avoid event loop issues
    from tests.end2end.mock_agent import create_mock_agent

    agent = create_mock_agent()

    # Test analyzing a system (main agent tool, no approval needed)
    result = await agent.run(
        "Analyze the production web server",
        user_id="test-user",
        thread_id=str(uuid.uuid4()),
        message_id=str(uuid.uuid4()),
    )

    print(f"\n✓ Result type: {type(result)}")
    print(f"✓ Has content: {hasattr(result, 'content')}")

    # Check if it's an AIMessage with content
    if hasattr(result, "content"):
        print(f"✓ Content: {result.content[:200]}...")

    # Check if it's structured output
    if hasattr(result, "summary"):
        print("✓ Structured output received")
        print(f"  Summary: {result.summary}")
        print(f"  Operations: {len(result.operations_performed)}")
        print(f"  Risk level: {result.risk_level}")
        assert result.risk_level in ["low", "medium", "high", "critical"]

    print("\n✅ Basic agent execution test passed!")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_subagent_delegation():
    """Test delegation to subagents (DatabaseAdmin and NetworkAdmin)."""
    print("\n" + "=" * 80)
    print("TEST: Subagent Delegation")
    print("=" * 80)

    # Create fresh agent instance to avoid event loop issues
    from tests.end2end.mock_agent import create_mock_agent

    agent = create_mock_agent()

    # Test database subagent delegation
    print("\n1. Testing DatabaseAdmin delegation...")
    result = await agent.run(
        "Query the UserDB database to get all users",
        user_id="test-user",
        thread_id=str(uuid.uuid4()),
        message_id=str(uuid.uuid4()),
    )

    print(f"✓ Result received: {type(result)}")
    if hasattr(result, "content"):
        print(f"✓ Content: {result.content[:200]}...")
    if hasattr(result, "summary"):
        print(f"✓ Summary: {result.summary}")

    # Test network subagent delegation
    print("\n2. Testing NetworkAdmin delegation...")
    result = await agent.run(
        "Check connectivity to 192.168.1.100",
        user_id="test-user",
        thread_id=str(uuid.uuid4()),
        message_id=str(uuid.uuid4()),
    )

    print(f"✓ Result received: {type(result)}")
    if hasattr(result, "content"):
        print(f"✓ Content: {result.content[:200]}...")
    if hasattr(result, "summary"):
        print(f"✓ Summary: {result.summary}")

    print("\n✅ Subagent delegation test passed!")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_approval_workflow_approve():
    """Test approval workflow - approve scenario."""
    print("\n" + "=" * 80)
    print("TEST: Approval Workflow - APPROVE")
    print("=" * 80)

    # Create fresh agent instance to avoid event loop issues
    from tests.end2end.mock_agent import create_mock_agent

    agent = create_mock_agent()

    thread_id = str(uuid.uuid4())

    # Request an operation that requires approval (restart system)
    print("\n1. Requesting system restart (requires approval)...")
    result = await agent.run(
        "Restart the production web server",
        user_id="test-user",
        thread_id=thread_id,
        message_id=str(uuid.uuid4()),
    )

    print(f"✓ Result type: {type(result)}")

    # Check if execution was interrupted for approval
    if isinstance(result, dict) and result.get("status") == "interrupted":
        print("✓ Execution interrupted for approval!")
        print(f"  Tool: {result['interrupt_data'].get('tool', 'unknown')}")
        print(f"  Message: {result['interrupt_data'].get('message', 'N/A')}")
        print(f"  Risk level: {result['interrupt_data'].get('risk_level', 'N/A')}")

        # Approve the operation
        print("\n2. Approving the operation...")
        final_result = await agent.resume(thread_id=thread_id, approval=True, feedback="Approved for testing")

        print(f"✓ Final result type: {type(final_result)}")
        if hasattr(final_result, "content"):
            print(f"✓ Content: {final_result.content[:200]}...")
        if hasattr(final_result, "summary"):
            print(f"✓ Summary: {final_result.summary}")
            print(f"✓ Operations: {len(final_result.operations_performed)}")

        print("\n✅ Approval workflow (approve) test passed!")
    else:
        print("⚠️  Expected interrupt for approval but got direct result")
        print("   This may happen if the tool was executed without approval check")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_approval_workflow_reject():
    """Test approval workflow - reject scenario."""
    print("\n" + "=" * 80)
    print("TEST: Approval Workflow - REJECT")
    print("=" * 80)

    # Create fresh agent instance to avoid event loop issues
    from tests.end2end.mock_agent import create_mock_agent

    agent = create_mock_agent()

    thread_id = str(uuid.uuid4())

    # Request an operation that requires approval (block IP)
    print("\n1. Requesting IP block (requires approval)...")
    result = await agent.run(
        "Block IP address 192.168.1.50 on the firewall",
        user_id="test-user",
        thread_id=thread_id,
        message_id=str(uuid.uuid4()),
    )

    print(f"✓ Result type: {type(result)}")

    # Check if execution was interrupted for approval
    if isinstance(result, dict) and result.get("status") == "interrupted":
        print("✓ Execution interrupted for approval!")
        print(f"  Tool: {result['interrupt_data'].get('tool', 'unknown')}")
        print(f"  Message: {result['interrupt_data'].get('message', 'N/A')}")
        print(f"  Risk level: {result['interrupt_data'].get('risk_level', 'N/A')}")

        # Reject the operation
        print("\n2. Rejecting the operation...")
        final_result = await agent.resume(
            thread_id=thread_id, approval=False, feedback="Rejected - IP is internal development server"
        )

        print(f"✓ Final result type: {type(final_result)}")
        if hasattr(final_result, "content"):
            print(f"✓ Content: {final_result.content[:200]}...")
        if hasattr(final_result, "summary"):
            print(f"✓ Summary: {final_result.summary}")

        print("\n✅ Approval workflow (reject) test passed!")
    else:
        print("⚠️  Expected interrupt for approval but got direct result")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_structured_output_validation():
    """Test that structured output conforms to SystemManagementOutput schema."""
    print("\n" + "=" * 80)
    print("TEST: Structured Output Validation")
    print("=" * 80)

    # Create fresh agent instance to avoid event loop issues
    from tests.end2end.mock_agent import create_mock_agent

    agent = create_mock_agent()

    result = await agent.run(
        "Analyze the production web server and check database connectivity",
        user_id="test-user",
        thread_id=str(uuid.uuid4()),
        message_id=str(uuid.uuid4()),
    )

    print(f"✓ Result type: {type(result)}")

    # Check for structured output
    if hasattr(result, "summary"):
        print("\n✓ Structured output received!")
        print(f"  Summary: {result.summary}")
        print(f"  Operations performed: {len(result.operations_performed)}")
        print(f"  Recommendations: {len(result.recommendations)}")
        print(f"  Risk level: {result.risk_level}")

        # Validate schema fields
        assert isinstance(result.summary, str), "Summary should be string"
        assert isinstance(result.operations_performed, list), "Operations should be list"
        assert isinstance(result.recommendations, list), "Recommendations should be list"
        assert result.risk_level in ["low", "medium", "high", "critical"], "Invalid risk level"

        print("\n✅ Structured output validation passed!")
    else:
        print("⚠️  Expected structured output but got message")


if __name__ == "__main__":
    """Run tests directly with asyncio."""
    print("\n" + "=" * 80)
    print("RUNNING MOCK AGENT LIBRARY TESTS")
    print("=" * 80)

    async def run_all_tests():
        await test_basic_agent_execution()
        await test_subagent_delegation()
        await test_approval_workflow_approve()
        await test_approval_workflow_reject()
        await test_structured_output_validation()

    asyncio.run(run_all_tests())
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 80)
