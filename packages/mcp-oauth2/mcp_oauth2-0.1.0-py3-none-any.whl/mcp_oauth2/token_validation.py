"""
Token validation module for OAuth2 MCP authorization library.

This module provides JWT token validation functionality including signature verification,
issuer/audience validation, and user information extraction.
"""

import base64
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)

from .exceptions import (
    JWKSError,
    NetworkError,
    TokenValidationError,
)
from .models import JWKS, AuthenticatedUser, JWKSCacheEntry, OAuth2Config
from .utils import (
    extract_user_claims,
    generate_cache_key,
    validate_issuer_audience,
    validate_jwt_format,
    validate_token_expiration,
    validate_token_issued_at,
)

logger = logging.getLogger(__name__)

# In-memory cache for JWKS
jwks_cache: dict[str, JWKSCacheEntry] = {}

# Cache statistics
cache_stats = {"hits": 0, "misses": 0, "errors": 0}


async def validate_access_token(token: str, config: OAuth2Config) -> AuthenticatedUser:
    """
    Validate JWT access token and return authenticated user.

    Args:
        token: JWT token string
        config: OAuth2 configuration

    Returns:
        AuthenticatedUser object with token claims

    Raises:
        TokenValidationError: If token validation fails
        JWKSError: If JWKS operations fail
        ConfigurationError: If configuration is invalid
    """
    try:
        logger.debug(f"Validating access token for issuer: {config.issuer}")

        # Step 1: Basic JWT format validation
        validate_jwt_format(token)

        # Step 2: Decode token header and payload (without verification)
        try:
            unverified_header = jwt.get_unverified_header(token)
            unverified_payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                },
            )
        except InvalidTokenError as e:
            raise TokenValidationError(
                f"Invalid JWT token format: {str(e)}", token_issue="invalid_format"
            ) from e

        # Step 3: Validate token expiration
        validate_token_expiration(unverified_payload.get("exp"))

        # Step 4: Validate token issued-at time
        validate_token_issued_at(unverified_payload.get("iat"))

        # Step 5: Validate issuer and audience
        validate_issuer_audience(
            unverified_payload.get("iss", ""),
            unverified_payload.get("aud", ""),
            config.issuer,
            config.audience,
        )

        # Step 6: Get JWKS and verify signature
        jwks = await get_cached_jwks(config)
        await _verify_token_signature(token, unverified_header, jwks)

        # Step 7: Extract and validate user claims
        user_claims = extract_user_claims(unverified_payload)

        # Step 8: Create AuthenticatedUser object
        user = AuthenticatedUser(
            sub=user_claims.get("sub", ""),
            email=user_claims.get("email"),
            name=user_claims.get("name"),
            aud=user_claims.get("aud"),
            iss=user_claims.get("iss"),
            exp=user_claims.get("exp"),
            iat=user_claims.get("iat"),
        )

        logger.debug(f"Token validation successful for user: {user.sub}")
        return user

    except TokenValidationError:
        # Re-raise token validation errors as-is
        raise
    except JWKSError as e:
        # Convert JWKS errors to TokenValidationError
        raise TokenValidationError(
            f"Token validation failed: {str(e)}", token_issue="jwks_error"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise TokenValidationError(
            f"Token validation failed: {str(e)}", token_issue="validation_error"
        ) from e


async def fetch_jwks(config: OAuth2Config) -> JWKS:
    """
    Fetch JWKS from the OAuth2 provider.

    Args:
        config: OAuth2 configuration

    Returns:
        JWKS object with signing keys

    Raises:
        JWKSError: If JWKS fetch fails
        NetworkError: If network request fails
    """
    jwks_uri = config.jwks_uri or f"{config.issuer}/.well-known/jwks.json"

    try:
        logger.debug(f"Fetching JWKS from: {jwks_uri}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()

        jwks_data = response.json()

        if not jwks_data.get("keys"):
            raise JWKSError(
                "JWKS response does not contain any keys",
                jwks_uri=jwks_uri,
            )

        jwks = JWKS(keys=jwks_data["keys"])
        logger.info(
            f"Successfully fetched JWKS with {len(jwks.keys)} keys from {jwks_uri}"
        )

        return jwks

    except httpx.TimeoutException as e:
        logger.error(f"Timeout fetching JWKS from {jwks_uri}: {e}")
        raise NetworkError(f"Timeout fetching JWKS from {jwks_uri}") from e
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching JWKS from {jwks_uri}: {e}")
        raise JWKSError(
            f"Failed to fetch JWKS: HTTP {e.response.status_code}",
            jwks_uri=jwks_uri,
        ) from e
    except httpx.RequestError as e:
        logger.error(f"Network error fetching JWKS from {jwks_uri}: {e}")
        raise NetworkError(f"Network error fetching JWKS from {jwks_uri}") from e
    except Exception as e:
        logger.error(f"Unexpected error fetching JWKS from {jwks_uri}: {e}")
        raise JWKSError(
            f"Unexpected error fetching JWKS: {str(e)}",
            jwks_uri=jwks_uri,
        ) from e


async def get_cached_jwks(config: OAuth2Config) -> JWKS:
    """
    Get JWKS from cache or fetch if not available/expired.

    Args:
        config: OAuth2 configuration

    Returns:
        JWKS object with signing keys

    Raises:
        JWKSError: If JWKS operations fail
    """
    cache_key = generate_cache_key(config.issuer, config.jwks_uri)

    # Check if we have a valid cached entry
    if cache_key in jwks_cache:
        cache_entry = jwks_cache[cache_key]
        if not cache_entry.is_expired():
            logger.debug(f"Using cached JWKS for issuer: {config.issuer}")
            cache_stats["hits"] += 1
            return cache_entry.jwks
        else:
            logger.debug(f"Cached JWKS expired for issuer: {config.issuer}")
            # Remove expired entry
            del jwks_cache[cache_key]

    # Fetch fresh JWKS
    logger.debug(f"Fetching fresh JWKS for issuer: {config.issuer}")
    cache_stats["misses"] += 1
    jwks = await fetch_jwks(config)

    # Cache the JWKS
    cache_entry = JWKSCacheEntry(
        jwks=jwks,
        cached_at=datetime.now(UTC),
        ttl_seconds=config.jwks_cache_ttl,
    )
    jwks_cache[cache_key] = cache_entry

    logger.debug(
        f"Cached JWKS for issuer: {config.issuer} (TTL: {config.jwks_cache_ttl}s)"
    )
    return jwks


async def _verify_token_signature(
    token: str, header: dict[str, Any], jwks: JWKS
) -> None:
    """
    Verify JWT token signature using JWKS.

    Args:
        token: JWT token string
        header: Token header (unverified)
        jwks: JWKS object with signing keys

    Raises:
        TokenValidationError: If signature verification fails
    """
    try:
        kid = header.get("kid")
        if not kid:
            raise TokenValidationError(
                "Token header missing 'kid' (key ID)", token_issue="missing_kid"
            )

        # Find the signing key
        signing_key = None
        for key_data in jwks.keys:
            if key_data.get("kid") == kid:
                signing_key = key_data
                break

        if not signing_key:
            raise TokenValidationError(
                f"No signing key found for kid: {kid}", token_issue="key_not_found"
            )

        # Verify the signature
        await _verify_signature_with_key(token, signing_key)

        logger.debug(f"Token signature verified successfully with key: {kid}")

    except TokenValidationError:
        # Re-raise token validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise TokenValidationError(
            f"Token signature verification failed: {str(e)}",
            token_issue="signature_verification_failed",
        ) from e


async def _verify_signature_with_key(token: str, signing_key: dict[str, Any]) -> None:
    """
    Verify JWT signature with a specific signing key.

    Args:
        token: JWT token string
        signing_key: Signing key data from JWKS

    Raises:
        TokenValidationError: If signature verification fails
    """
    try:
        kty = signing_key.get("kty")
        alg = signing_key.get("alg", "RS256")

        if kty == "RSA":
            await _verify_rsa_signature(token, signing_key, alg)
        else:
            raise TokenValidationError(
                f"Unsupported key type: {kty}", token_issue="unsupported_key_type"
            )

    except TokenValidationError:
        raise
    except Exception as e:
        logger.error(f"Signature verification with key failed: {e}")
        raise TokenValidationError(
            f"Signature verification failed: {str(e)}",
            token_issue="signature_verification_failed",
        ) from e


async def _verify_rsa_signature(
    token: str, signing_key: dict[str, Any], alg: str
) -> None:
    """
    Verify RSA signature for JWT token.

    Args:
        token: JWT token string
        signing_key: RSA signing key data
        alg: Algorithm (e.g., RS256)

    Raises:
        TokenValidationError: If RSA signature verification fails
    """
    try:
        # Extract RSA key components
        n = signing_key.get("n")
        e = signing_key.get("e")

        if not n or not e:
            raise TokenValidationError(
                "RSA key missing required components (n, e)",
                token_issue="invalid_rsa_key",
            )

        # Decode base64url encoded components
        try:
            n_bytes = base64.urlsafe_b64decode(n + "==")  # Add padding
            e_bytes = base64.urlsafe_b64decode(e + "==")  # Add padding
        except Exception as e:
            raise TokenValidationError(
                f"Failed to decode RSA key components: {str(e)}",
                token_issue="invalid_rsa_key_encoding",
            ) from e

        # Convert to integers
        try:
            n_int = int.from_bytes(n_bytes, byteorder="big")
            e_int = int.from_bytes(e_bytes, byteorder="big")
        except Exception as e:
            raise TokenValidationError(
                f"Failed to convert RSA key components to integers: {str(e)}",
                token_issue="invalid_rsa_key_format",
            ) from e

        # Create RSA public key
        try:
            public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key(
                default_backend()
            )
        except Exception as e:
            raise TokenValidationError(
                f"Failed to create RSA public key: {str(e)}",
                token_issue="invalid_rsa_key_structure",
            ) from e

        # Verify signature using PyJWT (more reliable than manual verification)
        try:
            # Decode and verify the token
            jwt.decode(
                token,
                key=public_key,
                algorithms=[alg],
                options={"verify_exp": False, "verify_aud": False, "verify_iss": False},
            )
        except ExpiredSignatureError:
            # This shouldn't happen since we check expiration separately
            raise TokenValidationError(
                "Token has expired", token_issue="token_expired"
            ) from None
        except InvalidSignatureError:
            raise TokenValidationError(
                "Token signature is invalid", token_issue="invalid_signature"
            ) from None
        except InvalidTokenError as e:
            raise TokenValidationError(
                f"Token validation failed: {str(e)}",
                token_issue="token_validation_failed",
            ) from e

    except TokenValidationError:
        raise
    except Exception as e:
        logger.error(f"RSA signature verification failed: {e}")
        raise TokenValidationError(
            f"RSA signature verification failed: {str(e)}",
            token_issue="rsa_verification_failed",
        ) from e


def clear_jwks_cache(issuer: str | None = None) -> None:
    """
    Clear JWKS cache for a specific issuer or all issuers.

    Args:
        issuer: Issuer to clear cache for, or None to clear all
    """
    if issuer:
        cache_key = generate_cache_key(issuer, None)
        if cache_key in jwks_cache:
            del jwks_cache[cache_key]
            logger.debug(f"Cleared JWKS cache for issuer: {issuer}")
    else:
        jwks_cache.clear()
        logger.debug("Cleared all JWKS cache entries")


async def get_jwks_cache_stats() -> dict[str, Any]:
    """
    Get JWKS cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    total_entries = len(jwks_cache)
    expired_entries = sum(1 for entry in jwks_cache.values() if entry.is_expired())

    return {
        "total_entries": total_entries,
        "expired_entries": expired_entries,
        "active_entries": total_entries - expired_entries,
        "cache_keys": list(jwks_cache.keys()),
        "stats": cache_stats,
    }


async def verify_token_signature(token: str, jwks: JWKS) -> None:
    """Verify token signature with JWKS (wrapper function for tests).

    Args:
        token: JWT token to verify
        jwks: JWKS containing signing keys

    Raises:
        TokenValidationError: If signature verification fails
    """
    # Decode token header to get key ID
    try:
        header = jwt.get_unverified_header(token)
    except Exception as e:
        raise TokenValidationError(
            f"Failed to decode token header: {str(e)}",
            token_issue="invalid_header",
        ) from e

    await _verify_token_signature(token, header, jwks)
