"""Tests for production-grade authentication system."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from broadie.server.credentials import check_credentials


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock()
    request.client = Mock()
    request.client.host = "192.168.1.100"
    request.headers = Mock()
    request.headers.get = Mock(return_value=None)
    return request


@pytest.fixture
def mock_settings():
    """Mock settings with test API keys."""
    with patch("broadie.server.credentials.settings") as mock:
        mock.API_KEYS = {"sk_test_valid_key_123456789012345678", "sk_prod_another_valid_key_1234567890"}
        mock.PLAYGROUND_ORIGINS = ["http://localhost:3000", "https://app.example.com"]
        yield mock


class TestLocalhostBypass:
    """Test localhost bypass for development."""

    def test_null_client_with_localhost(self, mock_request):
        """Handle null client gracefully."""
        mock_request.client = None
        with pytest.raises(HTTPException) as exc:
            check_credentials(mock_request, api_key=None)
        assert exc.value.status_code == 403


class TestAPIKeyValidation:
    """Test API key validation logic."""

    def test_valid_api_key(self, mock_request, mock_settings):
        """Valid API key should authenticate successfully."""
        assert (
            check_credentials(
                mock_request,
                api_key="Bearer sk_test_valid_key_123456789012345678",
            )
            is True
        )

    def test_valid_api_key_multiple_keys(self, mock_request, mock_settings):
        """Any valid key from the set should work."""
        assert (
            check_credentials(
                mock_request,
                api_key="Bearer sk_prod_another_valid_key_1234567890",
            )
            is True
        )

    def test_invalid_api_key(self, mock_request, mock_settings):
        """Invalid API key should be rejected."""
        with pytest.raises(HTTPException) as exc:
            check_credentials(mock_request, api_key="Bearer sk_invalid_key")
        assert exc.value.status_code == 403
        assert "Invalid API key" in exc.value.detail

    def test_missing_bearer_prefix(self, mock_request, mock_settings):
        """Missing Bearer prefix should be rejected."""
        with pytest.raises(HTTPException) as exc:
            check_credentials(mock_request, api_key="sk_test_valid_key_123456789012345678")
        assert exc.value.status_code == 403
        assert "malformed Authorization header" in exc.value.detail

    def test_empty_api_key(self, mock_request, mock_settings):
        """Empty API key should be rejected."""
        with pytest.raises(HTTPException) as exc:
            check_credentials(mock_request, api_key="Bearer ")
        assert exc.value.status_code == 403
        assert "Empty API key" in exc.value.detail

    def test_none_api_key(self, mock_request, mock_settings):
        """None API key should be rejected."""
        with pytest.raises(HTTPException) as exc:
            check_credentials(mock_request, api_key=None)
        assert exc.value.status_code == 403

    def test_whitespace_only_token(self, mock_request, mock_settings):
        """Whitespace-only token should be rejected."""
        with pytest.raises(HTTPException) as exc:
            check_credentials(mock_request, api_key="Bearer    ")
        assert exc.value.status_code == 403
        assert "Empty API key" in exc.value.detail


class TestNoAPIKeysConfigured:
    """Test behavior when no API keys are configured."""

    def test_no_keys_configured(self, mock_request):
        """Should fail closed when no keys configured."""
        with patch("broadie.server.credentials.settings") as mock_settings:
            mock_settings.API_KEYS = set()
            mock_settings.PLAYGROUND_ORIGINS = []

            with pytest.raises(HTTPException) as exc:
                check_credentials(mock_request, api_key="Bearer some_key")
            assert exc.value.status_code == 403
            assert "not configured" in exc.value.detail


class TestSecurityFeatures:
    """Test security-specific features."""

    def test_constant_time_comparison(self, mock_request, mock_settings):
        """Verify constant-time comparison is used (prevents timing attacks)."""
        with patch("broadie.server.credentials.secrets.compare_digest") as mock_compare:
            mock_compare.return_value = False

            with pytest.raises(HTTPException):
                check_credentials(
                    mock_request,
                    api_key="Bearer sk_invalid_key",
                )

            # Should have called compare_digest for each key
            assert mock_compare.call_count == len(mock_settings.API_KEYS)

    def test_case_sensitive_keys(self, mock_request, mock_settings):
        """API keys should be case-sensitive."""
        with pytest.raises(HTTPException):
            check_credentials(
                mock_request,
                api_key="Bearer SK_TEST_VALID_KEY_123456789012345678",  # uppercase
            )

    def test_token_whitespace_stripped(self, mock_request, mock_settings):
        """Whitespace should be stripped from tokens."""
        assert (
            check_credentials(
                mock_request,
                api_key="Bearer  sk_test_valid_key_123456789012345678  ",
            )
            is True
        )


class TestLogging:
    """Test audit logging behavior."""

    @patch("broadie.server.credentials.logger")
    def test_logs_invalid_key_attempt(self, mock_logger, mock_request, mock_settings):
        """Invalid key attempts should be logged."""
        with pytest.raises(HTTPException):
            check_credentials(mock_request, api_key="Bearer sk_invalid_key")

        mock_logger.warning.assert_called()
        call_args = str(mock_logger.warning.call_args)
        assert "Invalid API key attempt" in call_args

    @patch("broadie.server.credentials.logger")
    def test_logs_missing_header(self, mock_logger, mock_request, mock_settings):
        """Missing headers should be logged."""
        with pytest.raises(HTTPException):
            check_credentials(mock_request, api_key=None)

        mock_logger.warning.assert_called()
        call_args = str(mock_logger.warning.call_args)
        assert "Missing or malformed Authorization header" in call_args

    @patch("broadie.server.credentials.logger")
    def test_logs_successful_auth(self, mock_logger, mock_request, mock_settings):
        """Successful auth should be logged at debug level."""
        check_credentials(
            mock_request,
            api_key="Bearer sk_test_valid_key_123456789012345678",
        )

        mock_logger.debug.assert_called()
        call_args = str(mock_logger.debug.call_args)
        assert "Successful authentication" in call_args

    @patch("broadie.server.credentials.logger")
    def test_logs_client_host(self, mock_logger, mock_request, mock_settings):
        """Logs should include client host."""
        with pytest.raises(HTTPException):
            check_credentials(mock_request, api_key="Bearer invalid")

        call_args = str(mock_logger.warning.call_args)
        assert "192.168.1.100" in call_args

    @patch("broadie.server.credentials.logger")
    def test_logs_unknown_when_no_client(self, mock_logger, mock_request, mock_settings):
        """Should log 'unknown' when client is None."""
        mock_request.client = None

        with pytest.raises(HTTPException):
            check_credentials(mock_request, api_key=None)

        call_args = str(mock_logger.warning.call_args)
        assert "unknown" in call_args


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_bearer_case_sensitive(self, mock_request, mock_settings):
        """Bearer prefix should be case-sensitive."""
        with pytest.raises(HTTPException):
            check_credentials(mock_request, api_key="bearer sk_test_valid_key_123456789012345678")

    def test_multiple_bearer_prefixes(self, mock_request, mock_settings):
        """Multiple Bearer prefixes should fail."""
        with pytest.raises(HTTPException):
            check_credentials(
                mock_request,
                api_key="Bearer Bearer sk_test_valid_key_123456789012345678",
            )

    def test_special_characters_in_key(self, mock_request):
        """Special characters in keys should work."""
        with patch("broadie.server.credentials.settings") as mock_settings:
            mock_settings.API_KEYS = {"sk_test!@#$%^&*()_+-=[]{}|;:,.<>?"}

            assert (
                check_credentials(
                    mock_request,
                    api_key="Bearer sk_test!@#$%^&*()_+-=[]{}|;:,.<>?",
                )
                is True
            )

    def test_very_long_key(self, mock_request):
        """Very long keys should work."""
        long_key = "sk_" + "a" * 1000
        with patch("broadie.server.credentials.settings") as mock_settings:
            mock_settings.API_KEYS = {long_key}

            assert (
                check_credentials(
                    mock_request,
                    api_key=f"Bearer {long_key}",
                )
                is True
            )

    def test_empty_playground_origins(self, mock_request):
        """Empty playground origins should not affect API key validation."""
        with patch("broadie.server.credentials.settings") as mock_settings:
            mock_settings.API_KEYS = {"sk_test_valid_key_123456789012345678"}

            with pytest.raises(HTTPException):
                check_credentials(mock_request, api_key=None)
