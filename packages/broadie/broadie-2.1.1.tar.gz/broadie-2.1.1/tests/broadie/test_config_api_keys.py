"""Tests for API_KEYS configuration."""

import os
import warnings
from unittest.mock import patch


class TestAPIKeysConfiguration:
    """Test API_KEYS parsing and validation in Settings."""

    def test_single_api_key_parsed(self):
        """Single API_KEYS value should be parsed."""
        env = {"API_KEYS": "sk_test_key_123456789012345678901234", "API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            assert "sk_test_key_123456789012345678901234" in config.settings.API_KEYS

    def test_multiple_api_keys_parsed(self):
        """Comma-separated API_KEYS should be parsed."""
        env = {
            "API_KEYS": "sk_test_key_1234567890123456789012,sk_prod_key_1234567890123456789012",
            "API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            assert "sk_test_key_1234567890123456789012" in config.settings.API_KEYS
            assert "sk_prod_key_1234567890123456789012" in config.settings.API_KEYS

    def test_api_keys_with_whitespace(self):
        """Whitespace around keys should be stripped."""
        env = {
            "API_KEYS": "  sk_test_key_1234567890123456789012  ,  sk_prod_key_1234567890123456789012  ",
            "API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            assert "sk_test_key_1234567890123456789012" in config.settings.API_KEYS
            assert "sk_prod_key_1234567890123456789012" in config.settings.API_KEYS

    def test_empty_api_keys_string(self):
        """Empty API_KEYS string should result in empty set."""
        env = {"API_KEYS": "", "API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            assert config.settings.API_KEYS == set()

    def test_api_keys_with_empty_values(self):
        """Empty values in comma-separated list should be filtered."""
        env = {
            "API_KEYS": "sk_test_key_1234567890123456789012,,sk_prod_key_1234567890123456789012,",
            "API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            keys = config.settings.API_KEYS
            assert "sk_test_key_1234567890123456789012" in keys
            assert "sk_prod_key_1234567890123456789012" in keys
            assert len(keys) == 2

    def test_legacy_api_key_backward_compatibility(self):
        """Legacy API_KEY should be added to API_KEYS."""
        env = {
            "API_KEY": "sk_legacy_key_123456789012345678901",
            "API_KEYS": "",
        }
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            assert "sk_legacy_key_123456789012345678901" in config.settings.API_KEYS
            assert config.settings.API_KEY == "sk_legacy_key_123456789012345678901"

    def test_both_api_key_and_api_keys(self):
        """Both API_KEY and API_KEYS should be merged."""
        env = {
            "API_KEY": "sk_legacy_key_123456789012345678901",
            "API_KEYS": "sk_test_key_1234567890123456789012,sk_prod_key_1234567890123456789012",
        }
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            keys = config.settings.API_KEYS
            assert len(keys) == 3
            assert "sk_legacy_key_123456789012345678901" in keys
            assert "sk_test_key_1234567890123456789012" in keys
            assert "sk_prod_key_1234567890123456789012" in keys

    def test_api_keys_is_set_type(self):
        """API_KEYS should be a set for O(1) lookup."""
        env = {
            "API_KEYS": "sk_test_key_1234567890123456789012,sk_test_key_1234567890123456789012",
            "API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            assert isinstance(config.settings.API_KEYS, set)
            assert len(config.settings.API_KEYS) == 1  # Duplicates removed

    def test_short_api_key_warning(self):
        """API keys shorter than 32 chars should trigger warning."""
        env = {"API_KEYS": "short_key", "API_KEY": ""}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with patch.dict(os.environ, env, clear=False):
                from importlib import reload

                from broadie import config

                reload(config)
                assert any("too short" in str(warning.message).lower() for warning in w)

    def test_no_warning_for_valid_length_keys(self):
        """Keys with 32+ characters should not trigger warning."""
        env = {
            "API_KEYS": "sk_test_key_1234567890123456789012",
            "API_KEY": "",
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with patch.dict(os.environ, env, clear=False):
                from importlib import reload

                from broadie import config

                reload(config)
                key_warnings = [warning for warning in w if "too short" in str(warning.message).lower()]
                assert len(key_warnings) == 0

    def test_api_keys_masked_in_safe_dict(self):
        """API_KEYS should be masked in safe dict output."""
        env = {
            "API_KEYS": "sk_test_key_1234567890123456789012",
        }
        with patch.dict(os.environ, env, clear=False):
            from importlib import reload

            from broadie import config

            reload(config)
            safe_dict = config.settings.to_dict(safe=True)
            assert safe_dict.get("API_KEYS") == "***MASKED***"
