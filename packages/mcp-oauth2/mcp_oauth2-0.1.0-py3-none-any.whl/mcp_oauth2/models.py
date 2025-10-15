"""Data models for OAuth2 MCP authorization library."""

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class OAuth2Config(BaseModel):
    """OAuth2 provider configuration."""

    model_config = ConfigDict()

    issuer: str = Field(
        ...,
        description="OAuth2 provider issuer URL (must use HTTPS)",
        json_schema_extra={"example": "https://auth.example.com"},
    )
    audience: str = Field(
        ...,
        description="Expected token audience (MCP server URI, must use HTTPS)",
        json_schema_extra={"example": "https://mcp-server.example.com"},
    )
    client_id: str = Field(
        ...,
        description="OAuth2 client ID",
        json_schema_extra={"example": "mcp-server-client"},
    )
    jwks_uri: str | None = Field(
        None,
        description="JWKS endpoint URL (auto-discovered if not provided)",
        json_schema_extra={"example": "https://auth.example.com/.well-known/jwks.json"},
    )
    jwks_cache_ttl: int = Field(
        3600,
        description="JWKS cache TTL in seconds (default: 1 hour)",
        ge=1,
        le=86400,  # Max 24 hours
    )
    exempt_routes: list[str] = Field(
        default_factory=list,
        description="Routes exempt from authentication (supports wildcards)",
        json_schema_extra={"example": ["/health", "/docs", "/openapi.json"]},
    )

    @field_validator("issuer")
    @classmethod
    def validate_issuer(cls, v: str) -> str:
        """Validate issuer URL."""
        if not v.startswith("https://"):
            raise ValueError("Issuer must use HTTPS")
        if not v.strip():
            raise ValueError("Issuer cannot be empty")
        return v.rstrip("/")

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, v: str) -> str:
        """Validate audience URL."""
        if not v.startswith("https://"):
            raise ValueError("Audience must use HTTPS")
        if not v.strip():
            raise ValueError("Audience cannot be empty")
        return v.rstrip("/")

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate client ID."""
        if not v.strip():
            raise ValueError("Client ID cannot be empty")
        if len(v) > 255:
            raise ValueError("Client ID must be 255 characters or less")
        return v.strip()

    @field_validator("jwks_uri")
    @classmethod
    def validate_jwks_uri(cls, v: str | None) -> str | None:
        """Validate JWKS URI."""
        if v is None:
            return v
        if not v.startswith("https://"):
            raise ValueError("JWKS URI must use HTTPS")
        if not v.strip():
            raise ValueError("JWKS URI cannot be empty")
        return v.rstrip("/")

    @field_validator("jwks_cache_ttl")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL."""
        if v <= 0:
            raise ValueError("Cache TTL must be positive")
        return v

    @field_validator("exempt_routes")
    @classmethod
    def validate_exempt_routes(cls, v: list[str]) -> list[str]:
        """Validate exempt routes."""
        if not isinstance(v, list):
            raise ValueError("Exempt routes must be a list")

        for route in v:
            if not isinstance(route, str):
                raise ValueError("Each exempt route must be a string")
            if not route.strip():
                raise ValueError("Exempt route cannot be empty")
            # Basic validation for route patterns
            if route.startswith("/") and len(route) > 1:
                # Allow basic wildcard patterns
                if "*" in route and not route.endswith("*"):
                    raise ValueError("Wildcard routes must end with '*'")

        return [route.strip() for route in v if route.strip()]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issuer": "https://auth.example.com",
                "audience": "https://mcp-server.example.com",
                "client_id": "mcp-server-client",
                "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
                "jwks_cache_ttl": 3600,
                "exempt_routes": ["/health", "/docs"],
            }
        }
    )


class AuthenticatedUser(BaseModel):
    """Authenticated user context from OAuth2 token."""

    sub: str = Field(
        ...,
        description="Subject identifier (user ID)",
        json_schema_extra={"example": "user-123"},
    )
    email: str | None = Field(
        None,
        description="User email address",
        json_schema_extra={"example": "user@example.com"},
    )
    name: str | None = Field(
        None,
        description="User display name",
        json_schema_extra={"example": "John Doe"},
    )
    aud: str | None = Field(
        None,
        description="Token audience",
        json_schema_extra={"example": "https://mcp-server.example.com"},
    )
    iss: str | None = Field(
        None,
        description="Token issuer",
        json_schema_extra={"example": "https://auth.example.com"},
    )
    exp: int | None = Field(
        None,
        description="Token expiration time (Unix timestamp)",
        json_schema_extra={"example": 1609459200},
    )
    iat: int | None = Field(
        None,
        description="Token issued at time (Unix timestamp)",
        json_schema_extra={"example": 1609455600},
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format."""
        if v is not None:
            if not v.strip():
                raise ValueError("Email cannot be empty")
            # Basic email validation
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
        return v

    @field_validator("sub")
    @classmethod
    def validate_sub(cls, v: str) -> str:
        """Validate subject identifier."""
        if not v.strip():
            raise ValueError("Subject identifier cannot be empty")
        if len(v) > 255:
            raise ValueError("Subject identifier must be 255 characters or less")
        return v.strip()

    @field_validator("exp", "iat")
    @classmethod
    def validate_timestamps(cls, v: int | None) -> int | None:
        """Validate timestamps."""
        if v is not None and v <= 0:
            raise ValueError("Timestamp must be positive")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "user-123",
                "email": "user@example.com",
                "name": "John Doe",
                "aud": "https://mcp-server.example.com",
                "iss": "https://auth.example.com",
                "exp": 1609459200,
                "iat": 1609455600,
            }
        }
    )


class UserInfo(BaseModel):
    """Extended user information from JWT token."""

    sub: str = Field(
        ...,
        description="Subject identifier",
        json_schema_extra={"example": "user-123"},
    )
    email: str | None = Field(
        None,
        description="User email address",
        json_schema_extra={"example": "user@example.com"},
    )
    name: str | None = Field(
        None,
        description="User display name",
        json_schema_extra={"example": "John Doe"},
    )
    preferred_username: str | None = Field(
        None,
        description="Preferred username",
        json_schema_extra={"example": "johndoe"},
    )
    given_name: str | None = Field(
        None,
        description="Given name",
        json_schema_extra={"example": "John"},
    )
    family_name: str | None = Field(
        None,
        description="Family name",
        json_schema_extra={"example": "Doe"},
    )

    @field_validator("sub")
    @classmethod
    def validate_sub(cls, v: str) -> str:
        """Validate subject identifier."""
        if not v.strip():
            raise ValueError("Subject identifier cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "user-123",
                "email": "user@example.com",
                "name": "John Doe",
                "preferred_username": "johndoe",
                "given_name": "John",
                "family_name": "Doe",
            }
        }
    )


class JWKS(BaseModel):
    """JSON Web Key Set for token validation."""

    keys: list[dict[str, Any]] = Field(
        ...,
        description="List of JSON Web Keys",
        min_length=0,
    )

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate JWKS keys."""
        # Allow empty keys list for testing purposes
        if not v:
            return v

        for key in v:
            if not isinstance(key, dict):
                raise ValueError("Each key must be a dictionary")
            if "kid" not in key:
                raise ValueError("Each key must have a 'kid' (key ID)")
            if "kty" not in key:
                raise ValueError("Each key must have a 'kty' (key type)")
            if "use" not in key:
                raise ValueError("Each key must have a 'use' (key use)")

        return v

    def get_key_by_kid(self, kid: str) -> dict[str, Any] | None:
        """Get key by key ID.

        Args:
            kid: Key ID to search for

        Returns:
            Key dictionary if found, None otherwise
        """
        for key in self.keys:
            if key.get("kid") == kid:
                return key
        return None

    def get_keys_by_use(self, use: str) -> list[dict[str, Any]]:
        """Get keys by key use.

        Args:
            use: Key use to search for (e.g., 'sig', 'enc')

        Returns:
            List of keys with the specified use
        """
        return [key for key in self.keys if key.get("use") == use]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keys": [
                    {
                        "kid": "test-key-1",
                        "kty": "RSA",
                        "use": "sig",
                        "alg": "RS256",
                        "n": "test-modulus",
                        "e": "AQAB",
                    }
                ]
            }
        }
    )


class SigningKey(BaseModel):
    """Signing key for JWT validation."""

    kid: str = Field(
        ...,
        description="Key ID",
        json_schema_extra={"example": "test-key-1"},
    )
    kty: str = Field(
        ...,
        description="Key type (RSA, EC, oct)",
        json_schema_extra={"example": "RSA"},
    )
    use: str = Field(
        ...,
        description="Key use (sig, enc)",
        json_schema_extra={"example": "sig"},
    )
    alg: str | None = Field(
        None,
        description="Algorithm (RS256, ES256, etc.)",
        json_schema_extra={"example": "RS256"},
    )
    n: str | None = Field(
        None,
        description="RSA modulus (base64url encoded)",
    )
    e: str | None = Field(
        None,
        description="RSA exponent (base64url encoded)",
        json_schema_extra={"example": "AQAB"},
    )
    x: str | None = Field(
        None,
        description="EC x coordinate (base64url encoded)",
    )
    y: str | None = Field(
        None,
        description="EC y coordinate (base64url encoded)",
    )

    @field_validator("kty")
    @classmethod
    def validate_key_type(cls, v: str) -> str:
        """Validate key type."""
        supported_types = ["RSA", "EC", "oct"]
        if v not in supported_types:
            raise ValueError(f"Unsupported key type. Must be one of: {supported_types}")
        return v

    @field_validator("use")
    @classmethod
    def validate_key_use(cls, v: str) -> str:
        """Validate key use."""
        valid_uses = ["sig", "enc"]
        if v not in valid_uses:
            raise ValueError(f"Invalid key use. Must be one of: {valid_uses}")
        return v

    @field_validator("kid")
    @classmethod
    def validate_kid(cls, v: str) -> str:
        """Validate key ID."""
        if not v.strip():
            raise ValueError("Key ID cannot be empty")
        if len(v) > 255:
            raise ValueError("Key ID must be 255 characters or less")
        return v.strip()

    def is_rsa_key(self) -> bool:
        """Check if this is an RSA key."""
        return self.kty == "RSA" and self.n is not None and self.e is not None

    def is_ec_key(self) -> bool:
        """Check if this is an EC key."""
        return self.kty == "EC" and self.x is not None and self.y is not None

    def is_oct_key(self) -> bool:
        """Check if this is an octet string key."""
        return self.kty == "oct"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "kid": "test-key-1",
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        }
    )


class JWKSCacheEntry(BaseModel):
    """JWKS cache entry."""

    jwks: JWKS = Field(
        ...,
        description="Cached JWKS",
    )
    cached_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Cache timestamp",
    )
    ttl_seconds: int = Field(
        ...,
        description="Cache TTL in seconds",
        ge=1,
    )

    @field_validator("ttl_seconds")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        """Validate TTL."""
        if v <= 0:
            raise ValueError("TTL must be positive")
        return v

    def is_expired(self) -> bool:
        """Check if cache entry is expired.

        Returns:
            True if expired, False otherwise
        """
        age = (datetime.now(UTC) - self.cached_at).total_seconds()
        return age >= self.ttl_seconds

    def get_age_seconds(self) -> float:
        """Get cache entry age in seconds.

        Returns:
            Age in seconds
        """
        return (datetime.now(UTC) - self.cached_at).total_seconds()

    def get_remaining_ttl(self) -> float:
        """Get remaining TTL in seconds.

        Returns:
            Remaining TTL in seconds (negative if expired)
        """
        return self.ttl_seconds - self.get_age_seconds()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "jwks": {
                    "keys": [
                        {
                            "kid": "test-key-1",
                            "kty": "RSA",
                            "use": "sig",
                            "alg": "RS256",
                            "n": "test-modulus",
                            "e": "AQAB",
                        }
                    ]
                },
                "cached_at": "2021-01-01T00:00:00",
                "ttl_seconds": 3600,
            }
        }
    )


class TokenValidationResult(BaseModel):
    """Result of token validation."""

    is_valid: bool = Field(
        ...,
        description="Whether the token is valid",
    )
    user: AuthenticatedUser | None = Field(
        None,
        description="Authenticated user if token is valid",
    )
    error_code: str | None = Field(
        None,
        description="Error code if validation failed",
    )
    error_message: str | None = Field(
        None,
        description="Error message if validation failed",
    )

    @classmethod
    def success(cls, user: AuthenticatedUser) -> "TokenValidationResult":
        """Create a successful validation result.

        Args:
            user: Authenticated user

        Returns:
            Successful validation result
        """
        return cls(
            is_valid=True,
            user=user,
            error_code=None,
            error_message=None,
        )

    @classmethod
    def failure(
        cls,
        error_code: str,
        error_message: str,
    ) -> "TokenValidationResult":
        """Create a failed validation result.

        Args:
            error_code: Error code
            error_message: Error message

        Returns:
            Failed validation result
        """
        return cls(
            is_valid=False,
            user=None,
            error_code=error_code,
            error_message=error_message,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "user": {
                    "sub": "user-123",
                    "email": "user@example.com",
                    "name": "John Doe",
                },
                "error_code": None,
                "error_message": None,
            }
        }
    )
