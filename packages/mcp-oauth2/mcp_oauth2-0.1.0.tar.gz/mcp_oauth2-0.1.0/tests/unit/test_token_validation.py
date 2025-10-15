"""
Unit tests for token validation module.

Tests JWT token validation, signature verification, JWKS handling, and caching.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx
import jwt
import pytest

from mcp_oauth2.config import OAuth2Config
from mcp_oauth2.exceptions import JWKSError, NetworkError, TokenValidationError
from mcp_oauth2.models import JWKS, AuthenticatedUser
from mcp_oauth2.token_validation import (
    clear_jwks_cache,
    fetch_jwks,
    get_cached_jwks,
    get_jwks_cache_stats,
    validate_access_token,
    verify_token_signature,
)


class TestTokenValidation:
    """Test JWT token validation functionality."""

    @pytest.fixture
    def config(self):
        """Create test OAuth2 configuration."""
        return OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
        )

    @pytest.fixture
    def mock_jwks(self):
        """Create mock JWKS data."""
        return {
            "keys": [
                {
                    "kid": "test-key-1",
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-n-value",
                    "e": "AQAB",
                }
            ]
        }

    @pytest.fixture
    def valid_token(self, config):
        """Create a valid JWT token for testing."""
        now = datetime.now(UTC)
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "aud": config.audience,
            "iss": config.issuer,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }

        # Create a token with a dummy signature (we'll mock the verification)
        return jwt.encode(
            payload, "secret", algorithm="HS256", headers={"kid": "test-key-1"}
        )

    async def test_validate_access_token_success(self, config, valid_token):
        """Test successful token validation."""
        with (
            patch("mcp_oauth2.token_validation.get_cached_jwks") as mock_get_jwks,
            patch("mcp_oauth2.token_validation._verify_token_signature") as mock_verify,
        ):
            # Mock JWKS response
            from mcp_oauth2.models import JWKS

            mock_jwks = JWKS(
                keys=[
                    {
                        "kid": "test-key-1",
                        "kty": "RSA",
                        "use": "sig",
                        "alg": "RS256",
                        "n": "test-n-value",
                        "e": "AQAB",
                    }
                ]
            )
            mock_get_jwks.return_value = mock_jwks
            mock_verify.return_value = None

            # Mock the JWT decode to return our test payload
            with patch("jwt.decode") as mock_decode:
                mock_decode.return_value = {
                    "sub": "test-user-123",
                    "email": "test@example.com",
                    "name": "Test User",
                    "aud": config.audience,
                    "iss": config.issuer,
                    "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
                    "iat": int(datetime.now(UTC).timestamp()),
                }

                user = await validate_access_token(valid_token, config)

                assert isinstance(user, AuthenticatedUser)
                assert user.sub == "test-user-123"
                assert user.email == "test@example.com"
                assert user.name == "Test User"
                assert user.aud == config.audience
                assert user.iss == config.issuer

    async def test_validate_access_token_invalid_format(self, config):
        """Test token validation with invalid JWT format."""
        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token("invalid.token.format", config)

        assert "Invalid JWT token format" in str(exc_info.value)
        assert exc_info.value.error_code == "TOKEN_VALIDATION_ERROR"

    async def test_validate_access_token_expired(self, config):
        """Test token validation with expired token."""
        # Create expired token
        now = datetime.now(UTC)
        expired_payload = {
            "sub": "test-user-123",
            "aud": config.audience,
            "iss": config.issuer,
            "exp": int((now - timedelta(hours=1)).timestamp()),  # Expired 1 hour ago
            "iat": int((now - timedelta(hours=2)).timestamp()),
        }
        expired_token = jwt.encode(
            expired_payload, "secret", algorithm="HS256", headers={"kid": "test-key-1"}
        )

        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token(expired_token, config)

        assert "Token has expired" in str(exc_info.value)

    async def test_validate_access_token_wrong_issuer(self, config):
        """Test token validation with wrong issuer."""
        now = datetime.now(UTC)
        wrong_issuer_payload = {
            "sub": "test-user-123",
            "aud": config.audience,
            "iss": "https://wrong-provider.com",  # Wrong issuer
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        wrong_issuer_token = jwt.encode(
            wrong_issuer_payload, "secret", algorithm="HS256"
        )

        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token(wrong_issuer_token, config)

        assert "does not match configured issuer" in str(exc_info.value)

    async def test_validate_access_token_wrong_audience(self, config):
        """Test token validation with wrong audience."""
        now = datetime.now(UTC)
        wrong_audience_payload = {
            "sub": "test-user-123",
            "aud": "https://wrong-server.com",  # Wrong audience
            "iss": config.issuer,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        wrong_audience_token = jwt.encode(
            wrong_audience_payload, "secret", algorithm="HS256"
        )

        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token(wrong_audience_token, config)

        assert "does not match configured audience" in str(exc_info.value)

    async def test_validate_access_token_missing_sub(self, config):
        """Test token validation with missing subject claim."""
        now = datetime.now(UTC)
        missing_sub_payload = {
            # Missing 'sub' claim
            "email": "test@example.com",
            "aud": config.audience,
            "iss": config.issuer,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        missing_sub_token = jwt.encode(
            missing_sub_payload,
            "secret",
            algorithm="HS256",
            headers={"kid": "test-key-1"},
        )

        # Mock both JWKS fetch and signature verification
        with (
            patch("mcp_oauth2.token_validation.fetch_jwks") as mock_fetch_jwks,
            patch("mcp_oauth2.token_validation._verify_token_signature") as mock_verify,
        ):
            from mcp_oauth2.models import JWKS

            mock_jwks = JWKS(
                keys=[
                    {
                        "kid": "test-key-1",
                        "kty": "RSA",
                        "use": "sig",
                        "alg": "RS256",
                        "n": "test-n-value",
                        "e": "AQAB",
                    }
                ]
            )
            mock_fetch_jwks.return_value = mock_jwks
            mock_verify.return_value = None  # Signature verification passes

            with pytest.raises(TokenValidationError) as exc_info:
                await validate_access_token(missing_sub_token, config)

            assert "Input should be a valid string" in str(exc_info.value)


class TestJWKSHandling:
    """Test JWKS fetching and caching functionality."""

    @pytest.fixture
    def config(self):
        """Create test OAuth2 configuration."""
        return OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
        )

    @pytest.fixture
    def mock_jwks_response(self):
        """Create mock JWKS HTTP response."""
        return {
            "keys": [
                {
                    "kid": "test-key-1",
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-n-value",
                    "e": "AQAB",
                }
            ]
        }

    async def test_fetch_jwks_success(self, config, mock_jwks_response):
        """Test successful JWKS fetching."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            jwks = await fetch_jwks(config)

            assert isinstance(jwks, JWKS)
            assert len(jwks.keys) == 1
            assert jwks.keys[0]["kid"] == "test-key-1"

    async def test_fetch_jwks_http_error(self, config):
        """Test JWKS fetching with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=Mock()
            )
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(JWKSError) as exc_info:
                await fetch_jwks(config)

            assert "Failed to fetch JWKS" in str(exc_info.value)

    async def test_fetch_jwks_network_error(self, config):
        """Test JWKS fetching with network error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.RequestError("Network error")
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(NetworkError) as exc_info:
                await fetch_jwks(config)

            assert "Network error fetching JWKS" in str(exc_info.value)

    async def test_fetch_jwks_timeout(self, config):
        """Test JWKS fetching with timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(NetworkError) as exc_info:
                await fetch_jwks(config)

            assert "Timeout fetching JWKS" in str(exc_info.value)

    async def test_fetch_jwks_empty_keys(self, config):
        """Test JWKS fetching with empty keys."""
        empty_jwks_response = {"keys": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = empty_jwks_response
            mock_response.raise_for_status.return_value = None

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(JWKSError) as exc_info:
                await fetch_jwks(config)

            assert "JWKS response does not contain any keys" in str(exc_info.value)

    async def test_get_cached_jwks_cache_hit(self, config, mock_jwks_response):
        """Test JWKS caching with cache hit."""
        # Clear cache first
        clear_jwks_cache()

        with patch("mcp_oauth2.token_validation.fetch_jwks") as mock_fetch:
            mock_jwks = JWKS(keys=mock_jwks_response["keys"])
            mock_fetch.return_value = mock_jwks

            # First call should fetch from network
            jwks1 = await get_cached_jwks(config)
            assert mock_fetch.call_count == 1

            # Second call should use cache
            jwks2 = await get_cached_jwks(config)
            assert mock_fetch.call_count == 1  # Still 1, not called again
            assert jwks1 == jwks2

    async def test_get_cached_jwks_cache_expired(self, config, mock_jwks_response):
        """Test JWKS caching with expired cache."""
        # Clear cache first
        clear_jwks_cache()

        with (
            patch("mcp_oauth2.token_validation.fetch_jwks") as mock_fetch,
            patch("mcp_oauth2.models.JWKSCacheEntry.is_expired", return_value=True),
        ):
            mock_jwks = JWKS(keys=mock_jwks_response["keys"])
            mock_fetch.return_value = mock_jwks

            # Should fetch from network even if cache exists but is expired
            await get_cached_jwks(config)
            assert mock_fetch.call_count == 1

    async def test_clear_jwks_cache(self, config):
        """Test clearing JWKS cache."""
        # Add something to cache first
        with patch("mcp_oauth2.token_validation.fetch_jwks") as mock_fetch:
            mock_jwks = Mock()
            mock_fetch.return_value = mock_jwks
            await get_cached_jwks(config)

            # Verify cache has entries
            stats = await get_jwks_cache_stats()
            assert stats["total_entries"] > 0

            # Clear cache
            clear_jwks_cache()

            # Verify cache is empty
            stats = await get_jwks_cache_stats()
            assert stats["total_entries"] == 0

    async def test_get_jwks_cache_stats(self, config, mock_jwks_response):
        """Test JWKS cache statistics."""
        # Clear cache first
        clear_jwks_cache()

        with patch("mcp_oauth2.token_validation.fetch_jwks") as mock_fetch:
            mock_jwks = JWKS(keys=mock_jwks_response["keys"])
            mock_fetch.return_value = mock_jwks

            # Add entry to cache
            await get_cached_jwks(config)

            stats = await get_jwks_cache_stats()
            assert "total_entries" in stats
            assert "expired_entries" in stats
            assert "active_entries" in stats
            assert "cache_keys" in stats
            assert stats["total_entries"] == 1
            assert stats["active_entries"] == 1
            assert stats["expired_entries"] == 0


class TestSignatureVerification:
    """Test JWT signature verification functionality."""

    @pytest.fixture
    def mock_jwks(self):
        """Create mock JWKS for signature verification."""
        return JWKS(
            keys=[
                {
                    "kid": "test-key-1",
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-n-value",
                    "e": "AQAB",
                }
            ]
        )

    @pytest.fixture
    def token_header(self):
        """Create token header with key ID."""
        return {"kid": "test-key-1", "alg": "RS256"}

    async def test_verify_token_signature_success(self, mock_jwks, token_header):
        """Test successful signature verification."""
        with patch(
            "mcp_oauth2.token_validation._verify_signature_with_key"
        ) as mock_verify:
            mock_verify.return_value = None

            # Should not raise any exception
            await verify_token_signature(
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5LTEifQ.eyJzdWIiOiJ1c2VyMTIzIn0.test",
                mock_jwks,
            )

            mock_verify.assert_called_once()

    async def test_verify_token_signature_missing_kid(self, mock_jwks):
        """Test signature verification with missing key ID."""
        # Create a token with RS256 algorithm but no kid in header
        import jwt

        payload = {"sub": "user123"}
        # Create token with RS256 but no kid header
        token = jwt.encode(
            payload, "secret", algorithm="HS256"
        )  # We'll mock the header

        # Mock the header to not have kid
        with patch("jwt.get_unverified_header") as mock_header:
            mock_header.return_value = {"alg": "RS256"}  # Missing 'kid'

            with pytest.raises(TokenValidationError) as exc_info:
                await verify_token_signature(token, mock_jwks)

            assert "Token header missing 'kid'" in str(exc_info.value)

    async def test_verify_token_signature_key_not_found(self, mock_jwks):
        """Test signature verification with key not found."""
        # Create a token that will be properly decoded
        token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Im5vbmV4aXN0ZW50LWtleSIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.test"

        with pytest.raises(TokenValidationError) as exc_info:
            await verify_token_signature(token, mock_jwks)

        assert "No signing key found for kid" in str(exc_info.value)

    async def test_verify_token_signature_verification_failed(
        self, mock_jwks, token_header
    ):
        """Test signature verification failure."""
        with patch(
            "mcp_oauth2.token_validation._verify_signature_with_key"
        ) as mock_verify:
            mock_verify.side_effect = TokenValidationError(
                "Signature verification failed",
                token_issue="signature_verification_failed",
            )

            with pytest.raises(TokenValidationError) as exc_info:
                await verify_token_signature(
                    "eyJhbGciOiJIUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJ1c2VyMTIzIn0.test",
                    mock_jwks,
                )

            assert "Signature verification failed" in str(exc_info.value)
