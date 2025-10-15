"""Tests for configuration loading and validation."""

import os
from unittest.mock import patch

import pytest

from mcp_oauth2.config import load_config_from_dict, load_config_from_env
from mcp_oauth2.exceptions import ConfigurationError


class TestConfigLoading:
    """Test configuration loading from environment variables."""

    def test_load_config_from_env_success(self):
        """Test successful configuration loading from environment."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
            "OAUTH2_JWKS_URI": "https://test-provider.com/.well-known/jwks.json",
            "OAUTH2_JWKS_CACHE_TTL": "7200",
            "OAUTH2_EXEMPT_ROUTES": "/health,/status",
        }

        with patch.dict(os.environ, env_vars):
            config = load_config_from_env()

            assert config.issuer == "https://test-provider.com"
            assert config.audience == "https://test-server.com"
            assert config.client_id == "test-client-id"
            assert config.jwks_uri == "https://test-provider.com/.well-known/jwks.json"
            assert config.jwks_cache_ttl == 7200
            assert config.exempt_routes == ["/health", "/status"]

    def test_load_config_from_env_minimal(self):
        """Test configuration loading with only required fields."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

            assert config.issuer == "https://test-provider.com"
            assert config.audience == "https://test-server.com"
            assert config.client_id == "test-client-id"
            assert config.jwks_uri is None
            assert config.jwks_cache_ttl == 3600  # Default value
            assert config.exempt_routes == []

    def test_load_config_from_env_missing_issuer(self):
        """Test configuration loading with missing issuer."""
        env_vars = {
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "OAUTH2_ISSUER environment variable is required" in str(
                exc_info.value
            )
            assert exc_info.value.field == "issuer"

    def test_load_config_from_env_missing_audience(self):
        """Test configuration loading with missing audience."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "OAUTH2_AUDIENCE environment variable is required" in str(
                exc_info.value
            )
            assert exc_info.value.field == "audience"

    def test_load_config_from_env_missing_client_id(self):
        """Test configuration loading with missing client_id."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "OAUTH2_CLIENT_ID environment variable is required" in str(
                exc_info.value
            )
            assert exc_info.value.field == "client_id"

    def test_load_config_from_env_empty_issuer(self):
        """Test configuration loading with empty issuer."""
        env_vars = {
            "OAUTH2_ISSUER": "",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "OAUTH2_ISSUER environment variable is required" in str(
                exc_info.value
            )
            assert exc_info.value.field == "issuer"

    def test_load_config_from_env_empty_audience(self):
        """Test configuration loading with empty audience."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "",
            "OAUTH2_CLIENT_ID": "test-client-id",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "OAUTH2_AUDIENCE environment variable is required" in str(
                exc_info.value
            )
            assert exc_info.value.field == "audience"

    def test_load_config_from_env_empty_client_id(self):
        """Test configuration loading with empty client_id."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "OAUTH2_CLIENT_ID environment variable is required" in str(
                exc_info.value
            )
            assert exc_info.value.field == "client_id"

    def test_load_config_from_env_invalid_cache_ttl(self):
        """Test configuration loading with invalid cache TTL."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
            "OAUTH2_JWKS_CACHE_TTL": "invalid",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "Invalid configuration value" in str(exc_info.value)
            assert "invalid literal for int()" in str(
                exc_info.value.details["original_error"]
            )

    def test_load_config_from_env_exempt_routes_parsing(self):
        """Test exempt routes parsing from environment variable."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
            "OAUTH2_EXEMPT_ROUTES": "/health, /status , /metrics,",  # Various formats
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

            assert config.exempt_routes == ["/health", "/status", "/metrics"]

    def test_load_config_from_env_exempt_routes_empty_string(self):
        """Test exempt routes with empty string."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
            "OAUTH2_EXEMPT_ROUTES": "",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

            assert config.exempt_routes == []

    def test_load_config_from_env_exempt_routes_whitespace_only(self):
        """Test exempt routes with whitespace only."""
        env_vars = {
            "OAUTH2_ISSUER": "https://test-provider.com",
            "OAUTH2_AUDIENCE": "https://test-server.com",
            "OAUTH2_CLIENT_ID": "test-client-id",
            "OAUTH2_EXEMPT_ROUTES": "  , , ",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

            assert config.exempt_routes == []

    def test_load_config_from_env_general_exception(self):
        """Test configuration loading with general exception."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = Exception("Unexpected error")

            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()

            assert "Failed to load configuration" in str(exc_info.value)
            assert "Unexpected error" in str(exc_info.value.details["original_error"])


class TestConfigFromDict:
    """Test configuration loading from dictionary."""

    def test_load_config_from_dict_success(self):
        """Test successful configuration loading from dictionary."""
        config_dict = {
            "issuer": "https://test-provider.com",
            "audience": "https://test-server.com",
            "client_id": "test-client-id",
            "jwks_uri": "https://test-provider.com/.well-known/jwks.json",
            "jwks_cache_ttl": 7200,
            "exempt_routes": ["/health", "/status"],
        }

        config = load_config_from_dict(config_dict)

        assert config.issuer == "https://test-provider.com"
        assert config.audience == "https://test-server.com"
        assert config.client_id == "test-client-id"
        assert config.jwks_uri == "https://test-provider.com/.well-known/jwks.json"
        assert config.jwks_cache_ttl == 7200
        assert config.exempt_routes == ["/health", "/status"]

    def test_load_config_from_dict_minimal(self):
        """Test configuration loading from dictionary with minimal fields."""
        config_dict = {
            "issuer": "https://test-provider.com",
            "audience": "https://test-server.com",
            "client_id": "test-client-id",
        }

        config = load_config_from_dict(config_dict)

        assert config.issuer == "https://test-provider.com"
        assert config.audience == "https://test-server.com"
        assert config.client_id == "test-client-id"
        assert config.jwks_uri is None
        assert config.jwks_cache_ttl == 3600  # Default value
        assert config.exempt_routes == []

    def test_load_config_from_dict_invalid_data(self):
        """Test configuration loading from dictionary with invalid data."""
        config_dict = {
            "issuer": "invalid-url",
            "audience": "https://test-server.com",
            "client_id": "test-client-id",
        }

        with pytest.raises(ConfigurationError) as exc_info:
            load_config_from_dict(config_dict)

        # The error should be from OAuth2Config validation
        assert "Invalid configuration:" in str(exc_info.value)

    def test_load_config_from_dict_missing_required_fields(self):
        """Test configuration loading from dictionary with missing required fields."""
        config_dict = {
            "audience": "https://test-server.com",
            "client_id": "test-client-id",
        }

        with pytest.raises(ConfigurationError) as exc_info:
            load_config_from_dict(config_dict)

        # The error should be from OAuth2Config validation
        assert "Invalid configuration:" in str(exc_info.value)
