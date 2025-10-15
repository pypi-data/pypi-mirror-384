"""Configuration module for OAuth2 MCP authorization library."""

import os
from typing import Any

from .exceptions import ConfigurationError
from .models import OAuth2Config


def load_config_from_env() -> OAuth2Config:
    """Load OAuth2 configuration from environment variables.

    Returns:
        OAuth2Config instance loaded from environment variables

    Raises:
        ConfigurationError: If required environment variables are missing or invalid
    """
    try:
        # Required configuration
        issuer = os.getenv("OAUTH2_ISSUER")
        if not issuer:
            raise ConfigurationError(
                "OAUTH2_ISSUER environment variable is required",
                field="issuer",
            )

        audience = os.getenv("OAUTH2_AUDIENCE")
        if not audience:
            raise ConfigurationError(
                "OAUTH2_AUDIENCE environment variable is required",
                field="audience",
            )

        client_id = os.getenv("OAUTH2_CLIENT_ID")
        if not client_id:
            raise ConfigurationError(
                "OAUTH2_CLIENT_ID environment variable is required",
                field="client_id",
            )

        # Optional configuration
        jwks_uri = os.getenv("OAUTH2_JWKS_URI")
        jwks_cache_ttl = int(os.getenv("OAUTH2_JWKS_CACHE_TTL", "3600"))

        # Parse exempt routes from environment variable
        exempt_routes = []
        exempt_routes_env = os.getenv("OAUTH2_EXEMPT_ROUTES")
        if exempt_routes_env:
            exempt_routes = [
                route.strip() for route in exempt_routes_env.split(",") if route.strip()
            ]

        return OAuth2Config(
            issuer=issuer,
            audience=audience,
            client_id=client_id,
            jwks_uri=jwks_uri,
            jwks_cache_ttl=jwks_cache_ttl,
            exempt_routes=exempt_routes,
        )

    except ValueError as e:
        raise ConfigurationError(
            f"Invalid configuration value: {str(e)}",
            details={"original_error": str(e)},
        ) from e
    except ConfigurationError:
        # Re-raise ConfigurationError without modification
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load configuration: {str(e)}",
            details={"original_error": str(e)},
        ) from e


def load_config_from_dict(config_dict: dict[str, Any]) -> OAuth2Config:
    """Load OAuth2 configuration from a dictionary.

    Args:
        config_dict: Dictionary containing configuration values

    Returns:
        OAuth2Config instance loaded from dictionary

    Raises:
        ConfigurationError: If required configuration values are missing or invalid
    """
    try:
        return OAuth2Config(**config_dict)
    except ValueError as e:
        raise ConfigurationError(
            f"Invalid configuration: {str(e)}",
            details={"original_error": str(e)},
        ) from e
    except ConfigurationError:
        # Re-raise ConfigurationError without modification
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load configuration: {str(e)}",
            details={"original_error": str(e)},
        ) from e


def validate_config(config: OAuth2Config) -> None:
    """Validate OAuth2 configuration.

    Args:
        config: OAuth2Config instance to validate

    Raises:
        ConfigurationError: If configuration is invalid
    """
    if not config.issuer:
        raise ConfigurationError("Issuer is required", field="issuer")

    if not config.audience:
        raise ConfigurationError("Audience is required", field="audience")

    if not config.client_id:
        raise ConfigurationError("Client ID is required", field="client_id")

    # Validate issuer and audience are different
    if config.issuer == config.audience:
        raise ConfigurationError(
            "Issuer and audience must be different",
            field="audience",
        )

    # Validate exempt routes don't conflict with each other
    _validate_exempt_routes(config.exempt_routes)


def _validate_exempt_routes(exempt_routes: list[str]) -> None:
    """Validate exempt routes configuration.

    Args:
        exempt_routes: List of exempt route patterns

    Raises:
        ConfigurationError: If exempt routes are invalid
    """
    if not isinstance(exempt_routes, list):
        raise ConfigurationError(
            "Exempt routes must be a list",
            field="exempt_routes",
        )

    # Check for conflicting patterns
    for i, route1 in enumerate(exempt_routes):
        for j, route2 in enumerate(exempt_routes):
            if i != j and _routes_conflict(route1, route2):
                raise ConfigurationError(
                    f"Conflicting exempt routes: '{route1}' and '{route2}'",
                    field="exempt_routes",
                )


def _routes_conflict(route1: str, route2: str) -> bool:
    """Check if two route patterns conflict.

    Args:
        route1: First route pattern
        route2: Second route pattern

    Returns:
        True if routes conflict, False otherwise
    """
    # Simple conflict detection for basic patterns
    if route1 == route2:
        return True

    # Check if one route is a prefix of another with wildcard
    if route1.endswith("*") and route2.startswith(route1[:-1]):
        return True

    if route2.endswith("*") and route1.startswith(route2[:-1]):
        return True

    return False


def get_default_config() -> OAuth2Config:
    """Get default OAuth2 configuration for development/testing.

    Returns:
        Default OAuth2Config instance

    Note:
        This should only be used for development and testing.
        Production configurations should be loaded from environment variables
        or secure configuration management systems.
    """
    return OAuth2Config(
        issuer="https://auth.example.com",
        audience="https://mcp-server.example.com",
        client_id="default-client-id",
        jwks_uri="https://auth.example.com/.well-known/jwks.json",
        jwks_cache_ttl=3600,
        exempt_routes=["/health", "/docs", "/openapi.json"],
    )


def auto_discover_jwks_uri(issuer: str) -> str:
    """Auto-discover JWKS URI from issuer.

    Args:
        issuer: OAuth2 issuer URL

    Returns:
        Discovered JWKS URI

    Raises:
        ConfigurationError: If issuer URL is invalid or JWKS URI cannot be discovered
    """
    if not issuer.startswith("https://"):
        raise ConfigurationError(
            "Issuer must use HTTPS for JWKS discovery",
            field="issuer",
        )

    # Remove trailing slash if present
    issuer = issuer.rstrip("/")

    # Standard JWKS discovery path
    jwks_uri = f"{issuer}/.well-known/jwks.json"

    return jwks_uri


def create_config(
    issuer: str,
    audience: str,
    client_id: str,
    jwks_uri: str | None = None,
    jwks_cache_ttl: int = 3600,
    exempt_routes: list[str] | None = None,
) -> OAuth2Config:
    """Create OAuth2 configuration with optional auto-discovery.

    Args:
        issuer: OAuth2 issuer URL
        audience: Expected token audience
        client_id: OAuth2 client ID
        jwks_uri: Optional JWKS URI (auto-discovered if not provided)
        jwks_cache_ttl: JWKS cache TTL in seconds
        exempt_routes: Optional list of exempt routes

    Returns:
        OAuth2Config instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Auto-discover JWKS URI if not provided
    if jwks_uri is None:
        jwks_uri = auto_discover_jwks_uri(issuer)

    # Set default exempt routes if not provided
    if exempt_routes is None:
        exempt_routes = ["/health", "/docs", "/openapi.json"]

    config = OAuth2Config(
        issuer=issuer,
        audience=audience,
        client_id=client_id,
        jwks_uri=jwks_uri,
        jwks_cache_ttl=jwks_cache_ttl,
        exempt_routes=exempt_routes,
    )

    # Validate the configuration
    validate_config(config)

    return config
