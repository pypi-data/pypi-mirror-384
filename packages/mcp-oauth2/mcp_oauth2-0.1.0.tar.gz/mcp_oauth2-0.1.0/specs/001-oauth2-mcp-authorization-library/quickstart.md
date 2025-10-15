# Quickstart Guide: OAuth2 MCP Authorization Library

**Date**: 2025-01-27  
**Feature**: OAuth2 MCP Authorization Library  
**Phase**: 1 - Design & Contracts

## Overview

This quickstart guide demonstrates how to integrate OAuth2 authentication into your MCP server using the minimal, secure OAuth2 authorization library. The library provides simple middleware integration for FastAPI applications with automatic JWT token validation.

## Prerequisites

- Python 3.13.5+
- FastAPI application
- OAuth2 provider (e.g., Auth0, Keycloak, Entra ID)
- MCP server endpoints

## Installation

```bash
# Install the library
pip install mcp-oauth2

# Or using uv (recommended)
uv add mcp-oauth2
```

## Basic Setup

### 1. Import and Configure

```python
from fastapi import FastAPI
from mcp_oauth2 import OAuth2Middleware, OAuth2Config

app = FastAPI()

# Configure OAuth2 provider
config = OAuth2Config(
    issuer="https://your-oauth-provider.com",
    audience="https://your-mcp-server.com",
    client_id="your-mcp-server-client-id"
)

# Add OAuth2 middleware (protects all routes by default)
app.add_middleware(OAuth2Middleware, config=config)
```

### 2. Define MCP Endpoints

```python
from mcp_oauth2.models import AuthenticatedUser

@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest, user: AuthenticatedUser):
    """Execute an MCP tool with automatic OAuth2 authentication"""
    # user is automatically injected after token validation
    return await handle_tool_call(request, user.sub)

@app.get("/mcp/resources")
async def list_resources(user: AuthenticatedUser):
    """List MCP resources with automatic OAuth2 authentication"""
    # user is automatically injected after token validation
    return await get_user_resources(user.sub)
```

### 3. Handle MCP Requests

```python
from mcp_oauth2.models import ToolCallRequest

async def handle_tool_call(request: ToolCallRequest, user_id: str):
    """Handle tool execution with authenticated user context"""
    # Your MCP tool logic here
    result = await execute_tool(request.name, request.arguments, user_id)
    
    return {
        "content": [{"type": "text", "text": result}],
        "isError": False
    }

async def get_user_resources(user_id: str):
    """Get resources accessible to the authenticated user"""
    # Your MCP resource logic here
    resources = await fetch_user_resources(user_id)
    
    return {
        "resources": [
            {
                "uri": f"resource://{resource.id}",
                "name": resource.name,
                "description": resource.description
            }
            for resource in resources
        ]
    }
```

## Advanced Configuration

### Exempt Routes

```python
config = OAuth2Config(
    issuer="https://your-oauth-provider.com",
    audience="https://your-mcp-server.com",
    client_id="your-mcp-server-client-id",
    exempt_routes=["/health", "/metrics", "/docs"]
)
```

### Custom JWKS Configuration

```python
config = OAuth2Config(
    issuer="https://your-oauth-provider.com",
    audience="https://your-mcp-server.com",
    client_id="your-mcp-server-client-id",
    jwks_uri="https://your-oauth-provider.com/.well-known/jwks.json",
    jwks_cache_ttl=7200  # 2 hours
)
```

## OAuth2 Provider Setup

### Auth0 Example

```python
config = OAuth2Config(
    issuer="https://your-domain.auth0.com",
    audience="https://your-mcp-server.com",
    client_id="your-auth0-client-id"
)
```

### Keycloak Example

```python
config = OAuth2Config(
    issuer="https://your-keycloak.com/realms/your-realm",
    audience="https://your-mcp-server.com",
    client_id="your-keycloak-client-id"
)
```

### Entra ID Example

```python
config = OAuth2Config(
    issuer="https://login.microsoftonline.com/your-tenant-id/v2.0",
    audience="https://your-mcp-server.com",
    client_id="your-entra-id-client-id"
)
```

## Error Handling

The library automatically handles authentication errors with appropriate HTTP status codes:

```python
# 401 - Invalid or missing token
{
    "error": "Token validation failed: Invalid signature",
    "code": "TOKEN_VALIDATION_ERROR",
    "details": "The JWT token signature could not be verified"
}

# 403 - Valid token but insufficient permissions
{
    "error": "Insufficient permissions",
    "code": "INSUFFICIENT_PERMISSIONS",
    "details": "User does not have required permissions for this resource"
}

# 503 - JWKS service unavailable
{
    "error": "JWKS service unavailable",
    "code": "JWKS_ERROR",
    "details": "Unable to fetch signing keys from authorization server"
}
```

## Testing

### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient
from mcp_oauth2 import OAuth2Middleware, OAuth2Config

def test_authenticated_endpoint():
    app = FastAPI()
    config = OAuth2Config(
        issuer="https://test-provider.com",
        audience="https://test-server.com",
        client_id="test-client"
    )
    app.add_middleware(OAuth2Middleware, config=config)
    
    @app.get("/test")
    async def test_endpoint(user: AuthenticatedUser):
        return {"user_id": user.sub}
    
    client = TestClient(app)
    
    # Test with valid token
    response = client.get(
        "/test",
        headers={"Authorization": "Bearer valid-jwt-token"}
    )
    assert response.status_code == 200
    
    # Test without token
    response = client.get("/test")
    assert response.status_code == 401
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_real_oauth2_provider():
    """Test with real OAuth2 provider"""
    config = OAuth2Config(
        issuer="https://your-test-provider.com",
        audience="https://your-test-server.com",
        client_id="your-test-client-id"
    )
    
    # Test with real JWT token from provider
    user = await validate_token("real-jwt-token", config)
    assert user.sub is not None
    assert user.iss == config.issuer
    assert user.aud == config.audience
```

## Performance Considerations

### Caching

The library automatically caches JWKS with a 1-hour TTL:

```python
config = OAuth2Config(
    # ... other config ...
    jwks_cache_ttl=3600  # 1 hour (default)
)
```

### Monitoring

Monitor key metrics:

- Token validation latency (<100ms target)
- JWKS fetch latency (<500ms target)
- Cache hit ratio
- Error rates by type

## Security Best Practices

### 1. HTTPS Only

Ensure all communications use HTTPS:

```python
config = OAuth2Config(
    issuer="https://your-provider.com",  # Must use HTTPS
    audience="https://your-server.com",  # Must use HTTPS
    client_id="your-client-id"
)
```

### 2. Secure Token Storage

The library handles token validation automatically. For client-side token storage:

```python
# Store tokens securely (example for MCP clients)
import keyring

# Store token securely
keyring.set_password("mcp-oauth2", "your-server", jwt_token)

# Retrieve token securely
token = keyring.get_password("mcp-oauth2", "your-server")
```

### 3. Audience Validation

Always validate token audience:

```python
config = OAuth2Config(
    audience="https://your-specific-mcp-server.com",  # Specific audience
    # ... other config ...
)
```

## Troubleshooting

### Common Issues

**1. "Token validation failed: Invalid signature"**
- Check JWKS endpoint accessibility
- Verify token issuer matches configuration
- Ensure token hasn't expired

**2. "JWKS service unavailable"**
- Check network connectivity to OAuth2 provider
- Verify JWKS endpoint URL is correct
- Check OAuth2 provider service status

**3. "Invalid audience"**
- Verify token audience matches configured audience
- Check OAuth2 provider audience configuration
- Ensure audience URL is exact match

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_oauth2")
```

## Production Deployment

### Environment Variables

```bash
# .env file
OAUTH2_ISSUER=https://your-oauth-provider.com
OAUTH2_AUDIENCE=https://your-mcp-server.com
OAUTH2_CLIENT_ID=your-client-id
OAUTH2_JWKS_CACHE_TTL=3600
```

```python
import os
from mcp_oauth2 import OAuth2Config

config = OAuth2Config(
    issuer=os.getenv("OAUTH2_ISSUER"),
    audience=os.getenv("OAUTH2_AUDIENCE"),
    client_id=os.getenv("OAUTH2_CLIENT_ID"),
    jwks_cache_ttl=int(os.getenv("OAUTH2_JWKS_CACHE_TTL", "3600"))
)
```

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Next Steps

1. **Set up OAuth2 provider**: Configure your OAuth2 provider with appropriate scopes and audiences
2. **Implement MCP tools**: Define your MCP tools and resources
3. **Test authentication**: Verify token validation works with your provider
4. **Monitor performance**: Set up monitoring for authentication metrics
5. **Deploy securely**: Follow security best practices for production deployment

For more detailed information, see the [API Documentation](./contracts/oauth2-middleware-api.json) and [Data Model](./data-model.md).