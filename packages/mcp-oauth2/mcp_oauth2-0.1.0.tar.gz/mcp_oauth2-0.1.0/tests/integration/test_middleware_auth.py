"""
Integration tests for OAuth2 middleware authentication.

Tests middleware with actual JWT token validation, user context injection,
and error handling scenarios.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from mcp_oauth2 import OAuth2Config, OAuth2Middleware, get_authenticated_user
from mcp_oauth2.models import AuthenticatedUser


class TestMiddlewareAuthentication:
    """Test OAuth2 middleware authentication functionality."""

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
    def app(self, config):
        """Create FastAPI app with OAuth2 middleware."""
        app = FastAPI()
        app.add_middleware(OAuth2Middleware, config=config)
        return app

    @pytest.fixture
    def mock_jwks_response(self):
        """Create mock JWKS response."""
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

    def create_valid_token(self, config, **extra_claims):
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
            **extra_claims,
        }
        return jwt.encode(
            payload, "secret", algorithm="HS256", headers={"kid": "test-key-1"}
        )

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    @patch("mcp_oauth2.token_validation._verify_token_signature")
    def test_middleware_with_valid_token(
        self, mock_verify, mock_fetch_jwks, app, config, mock_jwks_response
    ):
        """Test middleware with valid JWT token."""
        # Setup mocks - return proper JWKS model instead of Mock
        from mcp_oauth2.models import JWKS

        mock_jwks = JWKS(**mock_jwks_response)
        mock_fetch_jwks.return_value = mock_jwks
        mock_verify.return_value = None

        # Create valid token
        token = self.create_valid_token(config)

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub, "email": user.email}

        client = TestClient(app)

        # Test with valid token
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    def test_middleware_with_invalid_token_signature(
        self, mock_fetch_jwks, app, config, mock_jwks_response
    ):
        """Test middleware with invalid token signature."""
        # Setup mocks
        mock_jwks = Mock()
        mock_fetch_jwks.return_value = mock_jwks

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test with invalid token (wrong signature)
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIn0.invalid"
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {invalid_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["code"] == "TOKEN_VALIDATION_ERROR"
        assert "WWW-Authenticate" in response.headers

    def test_middleware_with_missing_authorization_header(self, app):
        """Test middleware with missing Authorization header."""

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test without Authorization header
        response = client.get("/protected")

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["code"] == "MISSING_TOKEN"
        assert "WWW-Authenticate" in response.headers

    def test_middleware_with_invalid_authorization_format(self, app):
        """Test middleware with invalid Authorization header format."""

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test with invalid Authorization header formats
        test_cases = [
            "InvalidFormat",
            "Bearer",
            "Basic token",
            "TokenWithoutBearer",
        ]

        for auth_header in test_cases:
            response = client.get("/protected", headers={"Authorization": auth_header})

            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert data["code"] in ["TOKEN_VALIDATION_ERROR", "MISSING_TOKEN"]

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    def test_middleware_with_expired_token(
        self, mock_fetch_jwks, app, config, mock_jwks_response
    ):
        """Test middleware with expired JWT token."""
        # Setup mocks
        mock_jwks = Mock()
        mock_fetch_jwks.return_value = mock_jwks

        # Create expired token
        now = datetime.now(UTC)
        expired_payload = {
            "sub": "test-user-123",
            "aud": config.audience,
            "iss": config.issuer,
            "exp": int((now - timedelta(hours=1)).timestamp()),  # Expired 1 hour ago
            "iat": int((now - timedelta(hours=2)).timestamp()),
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test with expired token
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["code"] == "TOKEN_VALIDATION_ERROR"
        assert "expired" in data["error"].lower()

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    def test_middleware_with_wrong_audience(
        self, mock_fetch_jwks, app, config, mock_jwks_response
    ):
        """Test middleware with token having wrong audience."""
        # Setup mocks
        mock_jwks = Mock()
        mock_fetch_jwks.return_value = mock_jwks

        # Create token with wrong audience
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

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test with wrong audience token
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {wrong_audience_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["code"] == "TOKEN_VALIDATION_ERROR"
        assert "audience" in data["error"].lower()

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    def test_middleware_with_wrong_issuer(
        self, mock_fetch_jwks, app, config, mock_jwks_response
    ):
        """Test middleware with token having wrong issuer."""
        # Setup mocks
        mock_jwks = Mock()
        mock_fetch_jwks.return_value = mock_jwks

        # Create token with wrong issuer
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

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test with wrong issuer token
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {wrong_issuer_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["code"] == "TOKEN_VALIDATION_ERROR"
        assert "issuer" in data["error"].lower()

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    @patch("mcp_oauth2.token_validation._verify_token_signature")
    def test_middleware_user_context_injection(
        self, mock_verify, mock_fetch_jwks, app, config, mock_jwks_response
    ):
        """Test that middleware properly injects user context."""
        # Setup mocks - return proper JWKS model instead of Mock
        from mcp_oauth2.models import JWKS

        mock_jwks = JWKS(**mock_jwks_response)
        mock_fetch_jwks.return_value = mock_jwks
        mock_verify.return_value = None

        # Create valid token
        token = self.create_valid_token(config)

        @app.get("/user-info")
        async def user_info_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {
                "user_id": user.sub,
                "email": user.email,
                "name": user.name,
                "audience": user.aud,
                "issuer": user.iss,
                "expires_at": user.exp,
                "issued_at": user.iat,
            }

        client = TestClient(app)

        # Test user context injection
        response = client.get(
            "/user-info", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["audience"] == config.audience
        assert data["issuer"] == config.issuer
        assert data["expires_at"] is not None
        assert data["issued_at"] is not None

    def test_middleware_exempt_routes_bypass_authentication(self, app):
        """Test that exempt routes bypass authentication."""
        # Update config to include exempt routes
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            exempt_routes=["/health", "/public"],
        )

        # Create new app with updated config
        app = FastAPI()
        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @app.get("/public")
        async def public_endpoint():
            return {"message": "public data"}

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Exempt routes should work without authentication
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

        response = client.get("/public")
        assert response.status_code == 200
        assert response.json() == {"message": "public data"}

        # Protected route should still require authentication
        response = client.get("/protected")
        assert response.status_code == 401

    def test_middleware_error_response_format(self, app):
        """Test that middleware returns properly formatted error responses."""

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test error response format
        response = client.get("/protected")

        assert response.status_code == 401
        data = response.json()

        # Check required fields
        assert "error" in data
        assert "code" in data

        # Check error message format
        assert isinstance(data["error"], str)
        assert len(data["error"]) > 0

        # Check error code format
        assert isinstance(data["code"], str)
        assert data["code"] in ["MISSING_TOKEN", "TOKEN_VALIDATION_ERROR"]

        # Check WWW-Authenticate header
        assert "WWW-Authenticate" in response.headers
        assert "Bearer" in response.headers["WWW-Authenticate"]
        assert "realm=" in response.headers["WWW-Authenticate"]

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    def test_middleware_jwks_fetch_error(self, mock_fetch_jwks, app, config):
        """Test middleware behavior when JWKS fetch fails."""
        # Setup mock to raise JWKS error
        from mcp_oauth2.exceptions import JWKSError

        mock_fetch_jwks.side_effect = JWKSError("JWKS service unavailable")

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test with JWKS error - add kid header to avoid early validation error
        token = self.create_valid_token(config)
        # Add kid header to the token
        import jwt

        header = jwt.get_unverified_header(token)
        header["kid"] = "test-key-1"
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
            },
        )
        token = jwt.encode(payload, "secret", algorithm="HS256", headers=header)
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["code"] in [
            "JWKS_ERROR",
            "AUTHENTICATION_ERROR",
            "TOKEN_VALIDATION_ERROR",
        ]


class TestMiddlewarePerformance:
    """Test middleware performance characteristics."""

    @pytest.fixture
    def config(self):
        """Create test OAuth2 configuration."""
        return OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            jwks_cache_ttl=3600,  # 1 hour cache
        )

    def create_valid_token(self, config, **extra_claims):
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
            **extra_claims,
        }
        return jwt.encode(
            payload, "secret", algorithm="HS256", headers={"kid": "test-key-1"}
        )

    @pytest.fixture
    def mock_jwks_response(self):
        """Create mock JWKS response."""
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

    @patch("mcp_oauth2.token_validation.fetch_jwks")
    @patch("mcp_oauth2.token_validation._verify_token_signature")
    def test_middleware_caching_performance(
        self, mock_verify, mock_fetch_jwks, config, mock_jwks_response
    ):
        """Test that middleware uses JWKS caching for performance."""
        # Setup mocks - return proper JWKS model instead of Mock
        from mcp_oauth2.models import JWKS

        mock_jwks = JWKS(**mock_jwks_response)
        mock_fetch_jwks.return_value = mock_jwks
        mock_verify.return_value = None

        app = FastAPI()
        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Create valid token
        token = self.create_valid_token(config)

        # First request should fetch JWKS
        response1 = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 200
        assert mock_fetch_jwks.call_count == 1

        # Second request should use cached JWKS
        response2 = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code == 200
        assert mock_fetch_jwks.call_count == 1  # Still 1, not called again

    def test_middleware_exempt_route_performance(self, config):
        """Test that exempt routes have minimal overhead."""
        # Update config to include exempt route
        config.exempt_routes = ["/health"]

        app = FastAPI()
        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        client = TestClient(app)

        # Exempt route should be fast (no token validation)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

        # Should not require any Authorization header
        assert "WWW-Authenticate" not in response.headers
