"""Test configuration and fixtures for mcp-oauth2 tests."""

import asyncio
import json
import time
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from mcp_oauth2.config import OAuth2Config
from mcp_oauth2.models import JWKS, AuthenticatedUser, JWKSCacheEntry


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_oauth2_config() -> OAuth2Config:
    """Create a sample OAuth2 configuration for testing."""
    return OAuth2Config(
        issuer="https://auth.example.com",
        audience="https://mcp-server.example.com",
        client_id="test-client-id",
        jwks_uri="https://auth.example.com/.well-known/jwks.json",
        jwks_cache_ttl=3600,
        exempt_routes=["/health", "/docs"],
    )


@pytest.fixture
def sample_jwks() -> JWKS:
    """Create a sample JWKS for testing."""
    return JWKS(
        keys=[
            {
                "kid": "test-key-1",
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    )


@pytest.fixture
def sample_jwks_cache_entry(sample_jwks: JWKS) -> JWKSCacheEntry:
    """Create a sample JWKS cache entry for testing."""
    return JWKSCacheEntry(
        jwks=sample_jwks,
        cached_at=datetime.now(UTC),
        ttl_seconds=3600,
    )


@pytest.fixture
def sample_authenticated_user() -> AuthenticatedUser:
    """Create a sample authenticated user for testing."""
    return AuthenticatedUser(
        sub="user-123",
        email="user@example.com",
        name="Test User",
        aud="https://mcp-server.example.com",
        iss="https://auth.example.com",
        exp=int(time.time()) + 3600,
        iat=int(time.time()),
    )


@pytest.fixture
def sample_jwt_token(sample_authenticated_user: AuthenticatedUser) -> str:
    """Create a sample JWT token for testing."""
    # Note: This is a mock token for testing - in real usage, tokens would be signed
    payload = {
        "sub": sample_authenticated_user.sub,
        "email": sample_authenticated_user.email,
        "name": sample_authenticated_user.name,
        "aud": sample_authenticated_user.aud,
        "iss": sample_authenticated_user.iss,
        "exp": sample_authenticated_user.exp,
        "iat": sample_authenticated_user.iat,
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def mock_jwks_response(sample_jwks: JWKS) -> Response:
    """Create a mock JWKS HTTP response."""
    return Response(
        status_code=200,
        content=json.dumps({"keys": sample_jwks.keys}).encode(),
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def mock_httpx_client(mock_jwks_response: Response):
    """Create a mock httpx client for testing."""
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_jwks_response
    return mock_client


@pytest.fixture
def fastapi_app() -> FastAPI:
    """Create a FastAPI app for testing."""
    return FastAPI(title="Test MCP OAuth2 App")


@pytest.fixture
def test_client(fastapi_app: FastAPI) -> TestClient:
    """Create a test client for FastAPI app."""
    return TestClient(fastapi_app)


@pytest.fixture
def mock_jwt_decode():
    """Mock jwt.decode for testing."""
    with patch("mcp_oauth2.token_validation.jwt.decode") as mock:
        mock.return_value = {
            "sub": "user-123",
            "email": "user@example.com",
            "name": "Test User",
            "aud": "https://mcp-server.example.com",
            "iss": "https://auth.example.com",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        yield mock


@pytest.fixture
def mock_httpx_get():
    """Mock httpx.AsyncClient.get for testing."""
    with patch("httpx.AsyncClient.get") as mock:
        yield mock


@pytest.fixture
def mock_time():
    """Mock time.time() for consistent testing."""
    with patch("time.time") as mock:
        mock.return_value = 1609459200  # 2021-01-01 00:00:00 UTC
        yield mock


@pytest.fixture
def mock_datetime():
    """Mock datetime.utcnow() for consistent testing."""
    with patch("mcp_oauth2.models.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2021, 1, 1, 0, 0, 0)
        yield mock_datetime


@pytest.fixture
def expired_jwt_token() -> str:
    """Create an expired JWT token for testing."""
    payload = {
        "sub": "user-123",
        "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        "iat": int(time.time()) - 7200,  # Issued 2 hours ago
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def invalid_jwt_token() -> str:
    """Create an invalid JWT token for testing."""
    return "invalid.jwt.token"


@pytest.fixture
def mock_jwks_fetch_error():
    """Mock JWKS fetch error for testing."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        yield mock_get


@pytest.fixture
def mock_jwks_invalid_response():
    """Mock invalid JWKS response for testing."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = Response(
            status_code=404,
            content=b"Not Found",
            headers={"Content-Type": "text/plain"},
        )
        mock_get.return_value = mock_response
        yield mock_get


# Performance testing fixtures
@pytest.fixture
def performance_config() -> OAuth2Config:
    """Configuration optimized for performance testing."""
    return OAuth2Config(
        issuer="https://auth.example.com",
        audience="https://mcp-server.example.com",
        client_id="perf-test-client",
        jwks_cache_ttl=3600,  # 1 hour cache
    )


@pytest.fixture
def large_jwks() -> JWKS:
    """Create a large JWKS with multiple keys for performance testing."""
    keys = []
    for i in range(10):  # 10 keys for testing
        keys.append(
            {
                "kid": f"test-key-{i}",
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "n": f"test-modulus-{i}",
                "e": "AQAB",
            }
        )
    return JWKS(keys=keys)


# Integration testing fixtures
@pytest.fixture
async def real_oauth2_config() -> OAuth2Config:
    """Configuration for integration tests with real OAuth2 providers."""
    return OAuth2Config(
        issuer="https://dev-123456.us.auth0.com",
        audience="https://mcp-server.example.com",
        client_id="integration-test-client",
        jwks_uri="https://dev-123456.us.auth0.com/.well-known/jwks.json",
    )


@pytest.fixture
def auth_headers(sample_jwt_token: str) -> dict[str, str]:
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {sample_jwt_token}"}


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    """Create invalid authorization headers for testing."""
    return {"Authorization": "Bearer invalid.token"}


@pytest.fixture
def no_auth_headers() -> dict[str, str]:
    """Create headers without authorization for testing."""
    return {}


# Utility functions for tests
def create_mock_jwt_payload(
    sub: str = "user-123",
    exp: int | None = None,
    iat: int | None = None,
    aud: str = "https://mcp-server.example.com",
    iss: str = "https://auth.example.com",
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a mock JWT payload for testing."""
    now = int(time.time())
    return {
        "sub": sub,
        "exp": exp or (now + 3600),
        "iat": iat or now,
        "aud": aud,
        "iss": iss,
        **kwargs,
    }


def create_mock_jwt_token(payload: dict[str, Any], secret: str = "test-secret") -> str:
    """Create a mock JWT token for testing."""
    return jwt.encode(payload, secret, algorithm="HS256")


def assert_auth_error_response(response: Response, expected_code: str) -> None:
    """Assert that a response is an authentication error with the expected code."""
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == expected_code
    assert "WWW-Authenticate" in response.headers


def assert_service_unavailable_response(response: Response) -> None:
    """Assert that a response is a service unavailable error."""
    assert response.status_code == 503
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "JWKS_ERROR"


# Markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow
