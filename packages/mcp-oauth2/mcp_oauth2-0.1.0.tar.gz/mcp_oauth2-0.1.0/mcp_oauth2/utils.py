"""Utility functions for OAuth2 MCP authorization library."""

import hashlib
import re
import time
from typing import Any
from urllib.parse import urlparse

from fastapi.responses import JSONResponse

from .exceptions import ConfigurationError, TokenValidationError


def validate_url(url: str, require_https: bool = True) -> str:
    """Validate and normalize a URL.

    Args:
        url: URL to validate
        require_https: Whether to require HTTPS

    Returns:
        Normalized URL

    Raises:
        ConfigurationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ConfigurationError("URL cannot be empty")

    url = url.strip()

    if not url:
        raise ConfigurationError("URL cannot be empty")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ConfigurationError(f"Invalid URL format: {str(e)}") from e

    if not parsed.scheme:
        raise ConfigurationError("URL must include scheme")

    if require_https and parsed.scheme != "https":
        raise ConfigurationError("URL must use HTTPS")

    if not parsed.netloc:
        raise ConfigurationError("URL must include hostname")

    # Return the original URL (don't remove trailing slash)
    return url


def validate_jwt_format(token: str) -> None:
    """Validate basic JWT token format.

    Args:
        token: JWT token to validate

    Raises:
        TokenValidationError: If token format is invalid
    """
    if not token or not isinstance(token, str):
        raise TokenValidationError("Token cannot be empty")

    token = token.strip()

    if not token:
        raise TokenValidationError("Token cannot be empty")

    # JWT should have exactly 3 parts separated by dots
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenValidationError(
            "Invalid JWT format: must have 3 parts separated by dots",
            token_issue="invalid_format",
        )

    # Each part should be base64url encoded
    for i, part in enumerate(parts):
        if not part:
            raise TokenValidationError(
                f"Invalid JWT format: part {i + 1} is empty",
                token_issue="invalid_format",
            )

        # Basic base64url validation (alphanumeric, -, _)
        if not re.match(r"^[A-Za-z0-9_-]+$", part):
            raise TokenValidationError(
                f"Invalid JWT format: part {i + 1} contains invalid characters",
                token_issue="invalid_format",
            )


def extract_bearer_token(auth_header: str) -> str:
    """Extract Bearer token from Authorization header.

    Args:
        auth_header: Authorization header value

    Returns:
        Extracted Bearer token

    Raises:
        TokenValidationError: If Authorization header is invalid
    """
    if not auth_header or not isinstance(auth_header, str):
        raise TokenValidationError(
            "Authorization header is missing",
            token_issue="missing_header",
        )

    auth_header = auth_header.strip()

    if not auth_header:
        raise TokenValidationError(
            "Authorization header is missing",
            token_issue="missing_header",
        )

    # Check for Bearer scheme (case-insensitive)
    auth_lower = auth_header.lower()
    if not auth_lower.startswith("bearer "):
        raise TokenValidationError(
            "Authorization header must use Bearer scheme",
            token_issue="invalid_scheme",
        )

    # Extract token (preserve original case)
    token = auth_header[7:]  # Remove "Bearer " prefix

    if not token:
        raise TokenValidationError(
            "Authorization header is missing",
            token_issue="missing_token",
        )

    return token


def generate_cache_key(issuer: str, jwks_uri: str | None) -> str:
    """Generate cache key for JWKS.

    Args:
        issuer: OAuth2 issuer URL
        jwks_uri: JWKS URI (can be None)

    Returns:
        Cache key string
    """
    # Create a deterministic cache key based on issuer and JWKS URI
    key_data = f"{issuer}:{jwks_uri or ''}"

    # Generate SHA-256 hash for consistent key format
    return hashlib.sha256(key_data.encode("utf-8")).hexdigest()


def is_route_exempt(path: str, exempt_routes: list[str]) -> bool:
    """Check if a route is exempt from authentication.

    Args:
        path: Request path to check
        exempt_routes: List of exempt route patterns

    Returns:
        True if route is exempt, False otherwise
    """
    if not exempt_routes:
        return False

    # Normalize path
    normalized_path = path.strip()
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path

    for exempt_route in exempt_routes:
        if _matches_exempt_pattern(normalized_path, exempt_route):
            return True

    return False


def _matches_exempt_pattern(path: str, pattern: str) -> bool:
    """Check if a path matches an exempt route pattern.

    Args:
        path: Request path
        pattern: Exempt route pattern

    Returns:
        True if path matches pattern, False otherwise
    """
    # Exact match
    if path == pattern:
        return True

    # Wildcard match
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        if path.startswith(prefix):
            return True

    # Regex pattern match (if pattern contains regex)
    if pattern.startswith("^") and pattern.endswith("$"):
        try:
            return bool(re.match(pattern, path))
        except re.error:
            # Invalid regex, fall back to exact match
            return path == pattern

    return False


def validate_issuer_audience(
    token_issuer: str, token_audience: str, config_issuer: str, config_audience: str
) -> None:
    """Validate token issuer and audience against configuration.

    Args:
        token_issuer: Token issuer claim
        token_audience: Token audience claim
        config_issuer: Configured issuer
        config_audience: Configured audience

    Raises:
        TokenValidationError: If issuer or audience validation fails
    """
    if not token_issuer:
        raise TokenValidationError(
            "Token is missing issuer claim",
            token_issue="missing_issuer",
        )

    if not token_audience:
        raise TokenValidationError(
            "Token is missing audience claim",
            token_issue="missing_audience",
        )

    # Validate issuer
    if token_issuer != config_issuer:
        raise TokenValidationError(
            f"Token issuer '{token_issuer}' does not match configured issuer '{config_issuer}'",
            token_issue="invalid_issuer",
        )

    # Validate audience
    if token_audience != config_audience:
        raise TokenValidationError(
            f"Token audience '{token_audience}' does not match configured audience '{config_audience}'",
            token_issue="invalid_audience",
        )


def validate_token_expiration(exp_claim: int | float | None) -> None:
    """Validate token expiration.

    Args:
        exp_claim: Token expiration claim (Unix timestamp)

    Raises:
        TokenValidationError: If token is expired
    """
    if exp_claim is None:
        raise TokenValidationError(
            "Token is missing expiration claim",
            token_issue="missing_exp",
        )

    try:
        exp_time = float(exp_claim)
    except (ValueError, TypeError):
        raise TokenValidationError(
            "Token expiration claim is not a valid timestamp",
            token_issue="invalid_exp",
        ) from None

    current_time = time.time()

    if exp_time <= current_time:
        raise TokenValidationError(
            "Token has expired",
            token_issue="expired",
        )


def validate_token_issued_at(iat_claim: int | float | None) -> None:
    """Validate token issued at time.

    Args:
        iat_claim: Token issued at claim (Unix timestamp)

    Raises:
        TokenValidationError: If token issued at time is invalid
    """
    if iat_claim is None:
        return  # iat is optional

    try:
        iat_time = float(iat_claim)
    except (ValueError, TypeError):
        raise TokenValidationError(
            "Token issued at claim is not a valid timestamp",
            token_issue="invalid_iat",
        ) from None

    current_time = time.time()

    # Token cannot be issued in the future (with 5 minute tolerance for clock skew)
    if iat_time > current_time + 300:
        raise TokenValidationError(
            "Token issued at time is in the future",
            token_issue="future_iat",
        )


def extract_user_claims(token_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract user claims from JWT token payload.

    Args:
        token_payload: JWT token payload

    Returns:
        Dictionary of user claims
    """
    # Standard OIDC claims
    standard_claims = [
        "sub",
        "email",
        "name",
        "preferred_username",
        "given_name",
        "family_name",
        "aud",
        "iss",
        "exp",
        "iat",
    ]

    # Always include all standard claims, using None for missing ones
    user_claims = {}
    for claim in standard_claims:
        user_claims[claim] = token_payload.get(claim)

    return user_claims


def sanitize_for_api(data: Any) -> Any:
    """Sanitize data for API responses to prevent sensitive information leakage.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data safe for API responses (preserves original type)
    """
    if data is None:
        return None

    if isinstance(data, str):
        return data

    if isinstance(data, dict):
        # Sanitize dictionary by redacting sensitive keys
        sanitized = {}
        sensitive_keys = {"password", "secret", "token", "key", "auth"}

        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_for_api(value)

        return sanitized

    if isinstance(data, (list, tuple)):
        # Sanitize list/tuple
        sanitized_items = [sanitize_for_api(item) for item in data]
        return sanitized_items

    return data


def sanitize_for_logging(data: Any, max_length: int = 100) -> str:
    """Sanitize data for logging to prevent sensitive information leakage.

    Args:
        data: Data to sanitize
        max_length: Maximum length of sanitized string

    Returns:
        Sanitized string safe for logging
    """
    if data is None:
        return "None"

    if isinstance(data, str):
        # Truncate long strings
        if len(data) > max_length:
            return data[: max_length - 3] + "..."
        return data

    if isinstance(data, dict):
        # Sanitize dictionary by redacting sensitive keys
        sanitized = {}
        sensitive_keys = {"password", "secret", "token", "key", "auth"}

        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_for_logging(value, max_length)

        return str(sanitized)

    if isinstance(data, (list, tuple)):
        # Sanitize list/tuple
        sanitized_items = [sanitize_for_logging(item, max_length) for item in data]
        return str(sanitized_items)

    return str(data)


def format_error_response(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    status_code: int = 401,
) -> JSONResponse:
    """Format error response for API responses.

    Args:
        error_code: Error code
        message: Error message
        details: Optional error details
        status_code: HTTP status code

    Returns:
        FastAPI JSONResponse object
    """
    import time

    response_data = {
        "error": error_code,
        "message": message,
        "timestamp": time.time(),
    }

    if details:
        response_data["details"] = sanitize_for_api(details)

    response = JSONResponse(
        status_code=status_code,
        content=response_data,
        headers={"Content-Type": "application/json"},
    )

    # Add a json() method to make it compatible with test expectations
    response.json = lambda: response_data  # type: ignore[attr-defined]

    return response


def calculate_ttl_seconds(cached_at: float, ttl_seconds: int) -> int:
    """Calculate remaining TTL in seconds.

    Args:
        cached_at: Cache timestamp (Unix timestamp)
        ttl_seconds: Original TTL in seconds

    Returns:
        Remaining TTL in seconds (negative if expired)
    """
    current_time = time.time()
    age = current_time - cached_at
    remaining = ttl_seconds - age
    return int(remaining)


def is_https_url(url: str) -> bool:
    """Check if URL uses HTTPS.

    Args:
        url: URL to check

    Returns:
        True if URL uses HTTPS, False otherwise
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https"
    except Exception:
        return False


def normalize_path(path: str) -> str:
    """Normalize request path for consistent matching.

    Args:
        path: Request path

    Returns:
        Normalized path
    """
    if not path:
        return ""

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Remove trailing slash (except for root)
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return path


def validate_required_claims(
    payload: dict[str, Any], required_claims: list[str] | None = None
) -> None:
    """Validate that required claims are present in token payload.

    Args:
        payload: JWT token payload dictionary
        required_claims: List of required claim names. Defaults to ["sub"].

    Raises:
        TokenValidationError: If any required claims are missing
    """
    if required_claims is None:
        required_claims = ["sub"]
    missing_claims = []

    for claim in required_claims:
        if claim not in payload or not payload.get(claim):
            missing_claims.append(claim)

    if missing_claims:
        raise TokenValidationError(
            f"Token is missing required claims: {', '.join(missing_claims)}",
            token_issue="missing_claims",
        )


def is_exempt_route(path: str, exempt_routes: list[str]) -> bool:
    """Check if a route is exempt from authentication.

    Args:
        path: Request path to check
        exempt_routes: List of exempt route patterns

    Returns:
        True if route is exempt, False otherwise
    """
    if not exempt_routes:
        return False

    for pattern in exempt_routes:
        if _match_route_pattern(path, pattern):
            return True

    return False


def _match_route_pattern(path: str, pattern: str) -> bool:
    """Match a path against a route pattern.

    Supports exact matches and simple wildcards:
    - "/health" matches exactly "/health"
    - "/health/*" matches "/health/" and "/health/status"
    - "/docs/*" matches "/docs/" and "/docs/openapi.json"

    Args:
        path: Request path
        pattern: Pattern to match against

    Returns:
        True if path matches pattern, False otherwise
    """
    if not pattern:
        return False

    # Exact match
    if path == pattern:
        return True

    # Wildcard pattern
    if pattern.endswith("/*"):
        prefix = pattern[:-2]  # Remove "/*"
        return path.startswith(prefix)

    # Exact match with trailing slash normalization
    if pattern.endswith("/") and not path.endswith("/"):
        return path + "/" == pattern
    if not pattern.endswith("/") and path.endswith("/"):
        return path == pattern + "/"

    return False
