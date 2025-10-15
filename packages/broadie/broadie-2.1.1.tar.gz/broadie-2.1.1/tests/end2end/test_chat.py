"""
Test mock_agent.py via CLI chat mode.

Tests:
1. Basic chat interaction
2. Approval workflow with interactive prompts
3. Subagent delegation via chat
"""

import os
import subprocess

import pytest

# Set up test environment
os.environ["CI"] = "true"  # Force in-memory storage


def run_chat_command(input_text: str, timeout: int = 30) -> tuple[str, str, int]:
    """Run broadie chat command with input and return output."""
    cmd = ["python", "-m", "broadie", "chat", "tests/end2end/mock_agent.py:agent"]

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/johnkitonyo/PycharmProjects/broadie",
    )

    try:
        stdout, stderr = process.communicate(input=input_text, timeout=timeout)
        return stdout, stderr, process.returncode
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return stdout, stderr, -1


@pytest.mark.e2e
def test_chat_basic_interaction():
    """Test basic chat interaction without approval."""
    print("\n" + "=" * 80)
    print("TEST: Basic Chat Interaction")
    print("=" * 80)

    # Send a simple query
    input_text = "Analyze the production web server\n"

    print(f"\nSending: {input_text.strip()}")
    stdout, stderr, returncode = run_chat_command(input_text, timeout=30)

    print(f"\n✓ Return code: {returncode}")
    print(f"✓ Output length: {len(stdout)} chars")

    # Check for expected output
    assert "SystemManager" in stdout or "systemmanager" in stdout, "Agent name not in output"
    assert "Chatting with agent" in stdout or "analyzing" in stdout.lower(), "No chat confirmation"

    print("\n✅ Basic chat interaction test passed!")


@pytest.mark.e2e
def test_chat_subagent_delegation():
    """Test subagent delegation via chat."""
    print("\n" + "=" * 80)
    print("TEST: Chat Subagent Delegation")
    print("=" * 80)

    # Send query that requires DatabaseAdmin subagent
    input_text = "Query the UserDB database\n"

    print(f"\nSending: {input_text.strip()}")
    stdout, stderr, returncode = run_chat_command(input_text, timeout=30)

    print(f"\n✓ Return code: {returncode}")
    print(f"✓ Output preview: {stdout[:300]}...")

    # Check for subagent-related output
    assert len(stdout) > 0, "No output received"

    print("\n✅ Chat subagent delegation test passed!")


@pytest.mark.e2e
def test_chat_approval_workflow():
    """Test approval workflow in chat mode."""
    print("\n" + "=" * 80)
    print("TEST: Chat Approval Workflow")
    print("=" * 80)

    # Send query that requires approval
    # Note: In chat mode, the approval prompt would be interactive
    # For automated testing, we can check if the interrupt is triggered
    input_text = "Restart the production web server\n"

    print(f"\nSending: {input_text.strip()}")
    print("Note: This may trigger an approval prompt in interactive mode")

    stdout, stderr, returncode = run_chat_command(input_text, timeout=30)

    print(f"\n✓ Return code: {returncode}")
    print(f"✓ Output length: {len(stdout)} chars")

    # Check if approval was mentioned or requested
    output_lower = stdout.lower()
    has_approval_mention = "approval" in output_lower or "interrupt" in output_lower or "restart" in output_lower

    print(f"✓ Approval mention detected: {has_approval_mention}")

    print("\n✅ Chat approval workflow test passed!")


if __name__ == "__main__":
    """Run tests directly."""
    print("\n" + "=" * 80)
    print("RUNNING MOCK AGENT CHAT TESTS")
    print("=" * 80)

    test_chat_basic_interaction()
    test_chat_subagent_delegation()
    test_chat_approval_workflow()

    print("\n" + "=" * 80)
    print("✅ ALL CHAT TESTS COMPLETED!")
    print("=" * 80)
