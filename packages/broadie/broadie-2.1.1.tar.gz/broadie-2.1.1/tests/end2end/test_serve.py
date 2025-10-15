"""
Test mock_agent.py via REST API server (broadie serve).

Tests:
1. Server startup and health check
2. GET /info endpoint
3. POST /invoke endpoint (basic execution)
4. POST /invoke with approval required (approve scenario)
5. POST /invoke with approval required (reject scenario)
6. POST /resume endpoint
"""

import json
import os
import signal
import subprocess
import time

import pytest
import requests

# Set up test environment
os.environ["CI"] = "true"  # Force in-memory storage
os.environ["API_KEYS"] = os.getenv("API_KEYS", "sk_prod_test-key-123")

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8765
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
AGENT_PATH = "agent/systemmanager"

# Get API key for authentication
API_KEY = os.getenv("API_KEYS", "sk_prod_test-key-123").split(",")[0].strip()
AUTH_HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


class ServerProcess:
    """Context manager for broadie serve process."""

    def __init__(self):
        self.process = None

    def start(self):
        """Start the broadie serve server."""
        cmd = [
            "python",
            "-m",
            "broadie",
            "serve",
            "tests/end2end/mock_agent.py:agent",
            "--host",
            SERVER_HOST,
            "--port",
            str(SERVER_PORT),
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/Users/johnkitonyo/PycharmProjects/broadie",
        )

        # Wait for server to start
        print(f"Starting server on {BASE_URL}...")
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=1)
                if response.status_code == 200:
                    print(f"✓ Server started successfully after {i + 1} attempts")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)

        print(f"✗ Server failed to start after {max_retries} seconds")
        return False

    def stop(self):
        """Stop the broadie serve server."""
        if self.process:
            print("Stopping server...")
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            print("✓ Server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


@pytest.fixture(scope="module")
def server():
    """Start server for all tests in this module."""
    with ServerProcess() as srv:
        yield srv


@pytest.mark.e2e
def test_server_health(server):
    """Test server health endpoint."""
    print("\n" + "=" * 80)
    print("TEST: Server Health Check")
    print("=" * 80)

    response = requests.get(f"{BASE_URL}/health")

    print(f"✓ Status code: {response.status_code}")
    print(f"✓ Response: {response.json()}")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    print("\n✅ Server health test passed!")


@pytest.mark.e2e
def test_get_info(server):
    """Test GET /agent/{agent_id}/info endpoint."""
    print("\n" + "=" * 80)
    print("TEST: GET /info Endpoint")
    print("=" * 80)

    response = requests.get(f"{BASE_URL}/{AGENT_PATH}/info", headers=AUTH_HEADERS)

    print(f"✓ Status code: {response.status_code}")
    data = response.json()
    print(f"✓ Agent ID: {data.get('id')}")
    print(f"✓ Agent name: {data.get('name')}")
    print(f"✓ Tools: {len(data.get('tools', []))}")
    print(f"✓ Subagents: {len(data.get('subagents', []))}")

    assert response.status_code == 200
    assert data["name"] == "SystemManager"
    assert len(data["subagents"]) == 2  # DatabaseAdmin and NetworkAdmin

    print("\n✅ GET /info test passed!")


@pytest.mark.e2e
def test_invoke_basic(server):
    """Test POST /invoke endpoint with basic execution."""
    print("\n" + "=" * 80)
    print("TEST: POST /invoke - Basic Execution")
    print("=" * 80)

    payload = {
        "message": "Analyze the production web server",
        "user_id": "test-user",
    }

    print(f"\n✓ Request URL: {BASE_URL}/{AGENT_PATH}/invoke")
    print(f"✓ Request payload: {json.dumps(payload, indent=2)}")
    print(f"✓ Auth headers: {AUTH_HEADERS}")

    try:
        response = requests.post(
            f"{BASE_URL}/{AGENT_PATH}/invoke",
            json=payload,
            headers=AUTH_HEADERS,
            timeout=60,  # Increase timeout to 60 seconds
        )

        print(f"\n✓ Status code: {response.status_code}")
        print(f"✓ Response headers: {dict(response.headers)}")

        # Check if response is a Mock object (test framework issue)
        if hasattr(response, "_mock_name"):
            pytest.fail(
                "Received a Mock object instead of real HTTP response. "
                "This suggests the server may not be running or there's a test configuration issue."
            )

        print(f"✓ Raw response text: {response.text[:1000]}...")

        # Try to parse JSON
        try:
            data = response.json()
            print("\n✓ Parsed JSON successfully")
            print(f"✓ Response data: {json.dumps(data, indent=2)}")

            # Check if data is a Mock object
            if hasattr(data, "_mock_name"):
                pytest.fail(
                    "Parsed JSON is a Mock object instead of real data. This suggests the response.json() is mocked."
                )

            print(f"✓ Response keys: {list(data.keys())}")
        except Exception as e:
            print(f"\n✗ Failed to parse JSON: {e}")
            print(f"✗ Response type: {type(response)}")
            print(f"✗ Data type: {type(data) if 'data' in locals() else 'N/A'}")
            print(f"✗ Raw response: {response.text}")
            pytest.fail(f"Failed to parse JSON response: {e}")

        # Check response structure
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Check if this is the expected response format
        if data == {"success": True}:
            pytest.fail(
                f"Received unexpected response format: {data}\n"
                f"This suggests the server may not have initialized properly or "
                f"the endpoint is returning a placeholder response.\n"
                f"Check server logs for errors during agent initialization."
            )

        # API returns: {"agent": ..., "thread_id": ..., "status": "completed", "response": ...}
        assert "thread_id" in data, f"Missing thread_id in response. Keys: {list(data.keys())}, Data: {data}"
        assert "status" in data, f"Missing status in response. Keys: {list(data.keys())}, Data: {data}"

        thread_id = data.get("thread_id")
        status = data.get("status")
        print(f"\n✓ Thread ID: {thread_id}")
        print(f"✓ Status: {status}")

        # Check for response content
        if status == "completed":
            assert "response" in data, f"Missing response in completed status: {data}"
            print("✓ Response included in result")
        elif status == "interrupted":
            assert "interrupt_data" in data, f"Missing interrupt_data in interrupted status: {data}"
            print("⚠️  Execution was interrupted (may require approval)")

        print("\n✅ POST /invoke basic test passed!")

    except requests.exceptions.Timeout:
        pytest.fail(
            "Request timed out after 60 seconds. Server may be unresponsive or agent is taking too long to initialize."
        )
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Connection error: {e}. Server may not be running.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


@pytest.mark.e2e
def test_invoke_with_approval_approve(server):
    """Test POST /invoke with approval required - approve scenario."""
    print("\n" + "=" * 80)
    print("TEST: POST /invoke - Approval Required (APPROVE)")
    print("=" * 80)

    # Step 1: Request operation that requires approval
    payload = {
        "message": "Restart the production web server",
        "user_id": "test-user",
    }

    print(f"\n1. Requesting operation: {payload['message']}")

    response = requests.post(f"{BASE_URL}/{AGENT_PATH}/invoke", json=payload, headers=AUTH_HEADERS, timeout=30)

    print(f"✓ Status code: {response.status_code}")
    data = response.json()
    print(f"✓ Response keys: {list(data.keys())}")

    assert response.status_code == 200
    thread_id = data.get("thread_id")
    print(f"✓ Thread ID: {thread_id}")

    # Check if approval is required
    if data.get("status") == "interrupted" or "interrupt" in str(data).lower():
        print("✓ Approval required detected!")

        # Step 2: Approve the operation
        print("\n2. Approving the operation...")

        resume_payload = {"thread_id": thread_id, "approval": True, "feedback": "Approved for testing"}

        resume_response = requests.post(
            f"{BASE_URL}/{AGENT_PATH}/resume", json=resume_payload, headers=AUTH_HEADERS, timeout=30
        )

        print(f"✓ Resume status code: {resume_response.status_code}")
        resume_data = resume_response.json()
        print(f"✓ Resume response keys: {list(resume_data.keys())}")

        assert resume_response.status_code == 200

        print("\n✅ Approval workflow (approve) test passed!")
    else:
        print("⚠️  Expected approval interrupt but got direct response")
        print(f"   Response: {json.dumps(data, indent=2)[:500]}...")


@pytest.mark.e2e
def test_invoke_with_approval_reject(server):
    """Test POST /invoke with approval required - reject scenario."""
    print("\n" + "=" * 80)
    print("TEST: POST /invoke - Approval Required (REJECT)")
    print("=" * 80)

    # Step 1: Request operation that requires approval
    payload = {
        "message": "Block IP address 192.168.1.50 on the firewall",
        "user_id": "test-user",
    }

    print(f"\n1. Requesting operation: {payload['message']}")

    response = requests.post(f"{BASE_URL}/{AGENT_PATH}/invoke", json=payload, headers=AUTH_HEADERS, timeout=30)

    print(f"✓ Status code: {response.status_code}")
    data = response.json()
    print(f"✓ Response keys: {list(data.keys())}")

    assert response.status_code == 200
    thread_id = data.get("thread_id")
    print(f"✓ Thread ID: {thread_id}")

    # Check if approval is required
    if data.get("status") == "interrupted" or "interrupt" in str(data).lower():
        print("✓ Approval required detected!")

        # Step 2: Reject the operation
        print("\n2. Rejecting the operation...")

        resume_payload = {
            "thread_id": thread_id,
            "approval": False,
            "feedback": "Rejected - IP is internal development server",
        }

        resume_response = requests.post(
            f"{BASE_URL}/{AGENT_PATH}/resume", json=resume_payload, headers=AUTH_HEADERS, timeout=30
        )

        print(f"✓ Resume status code: {resume_response.status_code}")
        resume_data = resume_response.json()
        print(f"✓ Resume response keys: {list(resume_data.keys())}")

        assert resume_response.status_code == 200

        print("\n✅ Approval workflow (reject) test passed!")
    else:
        print("⚠️  Expected approval interrupt but got direct response")
        print(f"   Response: {json.dumps(data, indent=2)[:500]}...")


@pytest.mark.e2e
def test_invoke_subagent_delegation(server):
    """Test subagent delegation via API."""
    print("\n" + "=" * 80)
    print("TEST: POST /invoke - Subagent Delegation")
    print("=" * 80)

    # Test DatabaseAdmin subagent
    payload = {
        "message": "Query the UserDB database to get all users",
        "user_id": "test-user",
    }

    print(f"\n✓ Testing DatabaseAdmin delegation: {payload['message']}")

    response = requests.post(f"{BASE_URL}/{AGENT_PATH}/invoke", json=payload, headers=AUTH_HEADERS, timeout=30)

    print(f"✓ Status code: {response.status_code}")
    data = response.json()
    print(f"✓ Thread ID: {data.get('thread_id')}")

    assert response.status_code == 200

    # Test NetworkAdmin subagent
    payload2 = {
        "message": "Check connectivity to 192.168.1.100",
        "user_id": "test-user",
    }

    print(f"\n✓ Testing NetworkAdmin delegation: {payload2['message']}")

    response2 = requests.post(f"{BASE_URL}/{AGENT_PATH}/invoke", json=payload2, headers=AUTH_HEADERS, timeout=30)

    print(f"✓ Status code: {response2.status_code}")

    assert response2.status_code == 200

    print("\n✅ Subagent delegation test passed!")


if __name__ == "__main__":
    """Run tests directly."""
    print("\n" + "=" * 80)
    print("RUNNING MOCK AGENT SERVER TESTS")
    print("=" * 80)

    with ServerProcess() as server:
        test_server_health(server)
        test_get_info(server)
        test_invoke_basic(server)
        test_invoke_with_approval_approve(server)
        test_invoke_with_approval_reject(server)
        test_invoke_subagent_delegation(server)

    print("\n" + "=" * 80)
    print("✅ ALL SERVER TESTS COMPLETED!")
    print("=" * 80)
