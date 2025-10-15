"""Comprehensive tests for token validation functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import httpx
import jwt
import pytest

from mcp_oauth2.exceptions import JWKSError, TokenValidationError
from mcp_oauth2.models import JWKS, JWKSCacheEntry, OAuth2Config
from mcp_oauth2.token_validation import (
    clear_jwks_cache,
    fetch_jwks,
    get_cached_jwks,
    get_jwks_cache_stats,
    validate_access_token,
    verify_token_signature,
)
from mcp_oauth2.utils import (
    validate_token_expiration,
    validate_token_issued_at,
)


class TestTokenValidation:
    """Test token validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
        )

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    @patch("mcp_oauth2.token_validation._verify_token_signature")
    @patch("mcp_oauth2.token_validation.validate_token_expiration")
    @patch("mcp_oauth2.token_validation.validate_token_issued_at")
    async def test_validate_access_token_success(
        self, mock_iat, mock_exp, mock_verify, mock_fetch
    ):
        """Test successful token validation."""
        # Setup mocks
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
        mock_fetch.return_value = mock_jwks
        mock_verify.return_value = None
        mock_exp.return_value = None
        mock_iat.return_value = None

        # Create a valid token
        now = datetime.now(UTC)
        payload = {
            "sub": "user123",
            "aud": self.config.audience,
            "iss": self.config.issuer,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        token = jwt.encode(
            payload, "secret", algorithm="HS256", headers={"kid": "test-key-1"}
        )

        # Mock signature verification to succeed
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = payload
            result = await validate_access_token(token, self.config)

            assert result.sub == "user123"
            assert result.aud == self.config.audience
            assert result.iss == self.config.issuer

    async def test_validate_access_token_invalid_format(self):
        """Test token validation with invalid format."""
        with pytest.raises(TokenValidationError):
            await validate_access_token("invalid-token", self.config)

    async def test_validate_access_token_empty_token(self):
        """Test token validation with empty token."""
        with pytest.raises(TokenValidationError):
            await validate_access_token("", self.config)

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    @patch("jwt.get_unverified_header")
    @patch("jwt.decode")
    async def test_validate_access_token_jwks_error(
        self, mock_decode, mock_header, mock_fetch
    ):
        """Test token validation with JWKS error."""
        # Clear cache to avoid interference from other tests
        clear_jwks_cache()
        mock_fetch.side_effect = JWKSError("JWKS fetch failed")
        # Mock JWT decode to return the payload without verification
        now = datetime.now(UTC)
        payload = {
            "sub": "user123",
            "aud": self.config.audience,
            "iss": self.config.issuer,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        mock_decode.return_value = payload
        mock_header.return_value = {"kid": "test-key-1", "alg": "RS256"}

        # Create a valid JWT token that will pass format validation
        token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJ1c2VyMTIzIiwiYXVkIjoiaHR0cHM6Ly9tY3Atc2VydmVyLmV4YW1wbGUuY29tIiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmV4YW1wbGUuY29tIiwiZXhwIjoxNzM2NzQ4MDAwLCJpYXQiOjE3MzY3NDQ0MDB9.test"

        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token(token, self.config)

        assert "JWKS fetch failed" in str(exc_info.value)

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    @patch("jwt.decode")
    async def test_validate_access_token_signature_verification_error(
        self, mock_decode, mock_fetch
    ):
        """Test token validation with signature verification error."""
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
        mock_fetch.return_value = mock_jwks
        mock_decode.side_effect = jwt.InvalidTokenError("Invalid signature")

        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token(token, self.config)

        assert "Invalid signature" in str(exc_info.value)


class TestJWKSHandling:
    """Test JWKS handling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
        )

    @patch("httpx.AsyncClient.get")
    async def test_fetch_jwks_success(self, mock_get):
        """Test successful JWKS fetching."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
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
        mock_get.return_value = mock_response

        result = await fetch_jwks(self.config)

        assert isinstance(result, JWKS)
        assert len(result.keys) == 1
        assert result.keys[0]["kid"] == "test-key-1"

    @patch("httpx.AsyncClient.get")
    async def test_fetch_jwks_http_error(self, mock_get):
        """Test JWKS fetching with HTTP error."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(JWKSError) as exc_info:
            await fetch_jwks(self.config)

        assert "Failed to fetch JWKS" in str(exc_info.value)

    @patch("httpx.AsyncClient.get")
    async def test_fetch_jwks_network_error(self, mock_get):
        """Test JWKS fetching with network error."""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(JWKSError) as exc_info:
            await fetch_jwks(self.config)

        assert "Network error" in str(exc_info.value)

    async def test_get_cached_jwks_cache_hit(self):
        """Test getting JWKS from cache (cache hit)."""
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
        )

        # Setup cache
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

        cache_entry = JWKSCacheEntry(
            jwks=mock_jwks,
            cached_at=datetime.now(UTC),
            ttl_seconds=3600,
        )

        # Mock the cache with proper cache key
        from mcp_oauth2.utils import generate_cache_key

        cache_key = generate_cache_key(config.issuer, config.jwks_uri)
        with patch("mcp_oauth2.token_validation.jwks_cache", {cache_key: cache_entry}):
            result = await get_cached_jwks(config)
            assert result == mock_jwks

    async def test_get_cached_jwks_cache_miss(self):
        """Test getting JWKS from cache (cache miss)."""
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
        )

        with patch("mcp_oauth2.token_validation.jwks_cache", {}):
            with patch("mcp_oauth2.token_validation.fetch_jwks") as mock_fetch:
                mock_jwks = JWKS(keys=[])
                mock_fetch.return_value = mock_jwks
                result = await get_cached_jwks(config)
                assert result == mock_jwks

    async def test_get_cached_jwks_cache_expired(self):
        """Test getting JWKS from cache (expired)."""
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
        )

        # Setup expired cache entry
        expired_time = datetime.now(UTC) - timedelta(hours=2)
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

        cache_entry = JWKSCacheEntry(
            jwks=mock_jwks,
            cached_at=expired_time,
            ttl_seconds=3600,  # 1 hour TTL
        )

        from mcp_oauth2.utils import generate_cache_key

        cache_key = generate_cache_key(config.issuer, config.jwks_uri)
        with patch("mcp_oauth2.token_validation.jwks_cache", {cache_key: cache_entry}):
            with patch("mcp_oauth2.token_validation.fetch_jwks") as mock_fetch:
                fresh_jwks = JWKS(keys=[])
                mock_fetch.return_value = fresh_jwks
                result = await get_cached_jwks(config)
                assert result == fresh_jwks

    async def test_clear_jwks_cache(self):
        """Test clearing JWKS cache."""
        # Setup cache with some entries
        with patch(
            "mcp_oauth2.token_validation.jwks_cache",
            {"key1": "value1", "key2": "value2"},
        ):
            clear_jwks_cache()
            # Verify cache is cleared
            from mcp_oauth2.token_validation import jwks_cache

            assert len(jwks_cache) == 0

    async def test_get_jwks_cache_stats(self):
        """Test getting JWKS cache statistics."""
        # Mock cache stats
        with patch(
            "mcp_oauth2.token_validation.cache_stats",
            {"hits": 10, "misses": 5, "errors": 2},
        ):
            stats = await get_jwks_cache_stats()
            assert stats["stats"]["hits"] == 10
            assert stats["stats"]["misses"] == 5
            assert stats["stats"]["errors"] == 2
            assert "total_entries" in stats
            assert "expired_entries" in stats
            assert "active_entries" in stats
            assert "cache_keys" in stats


class TestTokenSignatureVerification:
    """Test token signature verification."""

    async def test_verify_token_signature_valid(self):
        """Test valid token signature verification."""
        # This is a basic test - in practice, you'd need proper RSA keys
        jwks = JWKS(
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

        # Mock jwt.decode to succeed
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = {"sub": "user123"}
            # Should not raise an exception
            await verify_token_signature(
                "eyJhbGciOiJIUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJ1c2VyMTIzIn0.test",
                jwks,
            )

    async def test_verify_token_signature_invalid_key_id(self):
        """Test token signature verification with invalid key ID."""
        jwks = JWKS(
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

        # Mock jwt.get_unverified_header to return different kid
        with patch("jwt.get_unverified_header") as mock_header:
            mock_header.return_value = {"kid": "wrong-key"}

            with pytest.raises(TokenValidationError) as exc_info:
                await verify_token_signature(
                    "eyJhbGciOiJIUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJ1c2VyMTIzIn0.test",
                    jwks,
                )

            assert "No signing key found for kid" in str(exc_info.value)

    async def test_verify_token_signature_no_key_id(self):
        """Test token signature verification with no key ID."""
        jwks = JWKS(
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

        # Mock jwt.get_unverified_header to return no kid
        with patch("jwt.get_unverified_header") as mock_header:
            mock_header.return_value = {}

            with pytest.raises(TokenValidationError) as exc_info:
                await verify_token_signature(
                    "eyJhbGciOiJIUzI1NiIsImtpZCI6InRlc3Qta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJ1c2VyMTIzIn0.test",
                    jwks,
                )

            assert "Token header missing 'kid'" in str(exc_info.value)


class TestTokenExpirationValidation:
    """Test token expiration validation."""

    def test_validate_token_expiration_valid(self):
        """Test valid token expiration."""
        future_time = int((datetime.now(UTC) + timedelta(hours=1)).timestamp())
        # Should not raise an exception
        validate_token_expiration(future_time)

    def test_validate_token_expiration_expired(self):
        """Test expired token."""
        past_time = int((datetime.now(UTC) - timedelta(hours=1)).timestamp())

        with pytest.raises(TokenValidationError) as exc_info:
            validate_token_expiration(past_time)

        assert "Token has expired" in str(exc_info.value)

    def test_validate_token_expiration_missing(self):
        """Test token with missing expiration."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_token_expiration(None)

        assert "Token is missing expiration claim" in str(exc_info.value)

    def test_validate_token_expiration_invalid_type(self):
        """Test token with invalid expiration type."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_token_expiration("not-a-number")

        assert "Token expiration claim is not a valid timestamp" in str(exc_info.value)


class TestTokenIssuedAtValidation:
    """Test token issued at validation."""

    def test_validate_token_issued_at_valid(self):
        """Test valid token issued at time."""
        now = int(datetime.now(UTC).timestamp())
        # Should not raise an exception
        validate_token_issued_at(now)

    def test_validate_token_issued_at_future(self):
        """Test token issued in the future."""
        future_time = int((datetime.now(UTC) + timedelta(minutes=6)).timestamp())

        with pytest.raises(TokenValidationError) as exc_info:
            validate_token_issued_at(future_time)

        assert "Token issued at time is in the future" in str(exc_info.value)

    def test_validate_token_issued_at_missing(self):
        """Test token with missing issued at time."""
        # iat is optional, so None should not raise an error
        validate_token_issued_at(None)

    def test_validate_token_issued_at_invalid_type(self):
        """Test token with invalid issued at type."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_token_issued_at("not-a-number")

        assert "Token issued at claim is not a valid timestamp" in str(exc_info.value)


class TestTokenValidationEdgeCases:
    """Test token validation edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
        )

    async def test_validate_access_token_none_config(self):
        """Test token validation with None config."""
        with pytest.raises(TokenValidationError):
            await validate_access_token("token", None)

    async def test_validate_access_token_malformed_token(self):
        """Test token validation with malformed token."""
        with pytest.raises(TokenValidationError):
            await validate_access_token("not.a.jwt", self.config)

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    async def test_validate_access_token_empty_jwks(self, mock_fetch):
        """Test token validation with empty JWKS."""
        mock_jwks = JWKS(keys=[])
        mock_fetch.return_value = mock_jwks

        # Create a token with all required claims so it reaches the JWKS step
        now = datetime.now(UTC)
        payload = {
            "sub": "user123",
            "aud": self.config.audience,
            "iss": self.config.issuer,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        token = jwt.encode(
            payload, "secret", algorithm="HS256", headers={"kid": "test-key-1"}
        )

        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token(token, self.config)

        assert "No signing key found for kid" in str(exc_info.value)

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    async def test_validate_access_token_missing_kid_header(self, mock_fetch):
        """Test token validation with missing kid in header."""
        # Create a token with all required claims so it reaches the signature verification step
        now = datetime.now(UTC)
        payload = {
            "sub": "user123",
            "aud": self.config.audience,
            "iss": self.config.issuer,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        token = jwt.encode(
            payload,
            "secret",
            algorithm="HS256",
            # No headers with kid
        )

        # Mock JWKS with a key that won't match the token (since token has no kid)
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
        mock_fetch.return_value = mock_jwks

        with pytest.raises(TokenValidationError) as exc_info:
            await validate_access_token(token, self.config)

        assert "Token header missing 'kid'" in str(exc_info.value)
