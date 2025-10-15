"""Pytest configuration for end-to-end tests.

End-to-end tests need to make real HTTP requests, so we disable
the auto-mocking that's enabled for unit tests.
"""

import pytest


@pytest.fixture(autouse=True)
def auto_mock_external_deps():
    """Override parent conftest's auto-mocking - end2end tests need real HTTP calls."""
    yield None
