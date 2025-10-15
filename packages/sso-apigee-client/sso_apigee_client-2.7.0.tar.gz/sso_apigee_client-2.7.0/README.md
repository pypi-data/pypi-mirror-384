# SSO APIGEE Client

A comprehensive Python SDK for integrating with the SSO APIGEE Service, providing JWT-based stateless authentication with MOMRAH SSO and APIGEE API Gateway functionality.

## Features

- 🔐 **MOMRAH SSO Integration**: Complete OAuth2/OIDC authentication flow with JWT tokens
- 🚀 **APIGEE API Gateway**: Token management and API proxying
- ⚡ **FastAPI Integration**: Ready-to-use routers and dependencies
- 🔒 **JWT Security**: Stateless authentication, JWKS validation, secure token handling
- 🛠️ **Developer Friendly**: Simple API, comprehensive error handling
- 📦 **Production Ready**: Docker support, health checks, monitoring
- 🏛️ **Ministry-Grade**: Security features for government applications

## Installation

### Basic Installation

```bash
pip install sso-apigee-client
```

### With FastAPI Support

```bash
pip install sso-apigee-client[fastapi]
```

### Development Installation

```bash
pip install sso-apigee-client[dev]
```

## Quick Start

### 1. Basic Usage

```python
from sso_apigee_client import ApigeeClient, MOMRAHSSOClient

# Initialize APIGEE client
apigee_client = ApigeeClient(
    base_url="http://localhost:3300",
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret"
)

# Initialize MOMRAH SSO client
sso_client = MOMRAHSSOClient(
    service_url="http://localhost:3300",
    redirect_uri="https://myapp.com/auth/callback"
)

# Get APIGEE token
token = await apigee_client.get_token()
print(f"Access token: {token.access_token}")

# Get MOMRAH SSO login URL
login_url = await sso_client.get_login_url()
print(f"Login URL: {login_url}")
```

### 2. FastAPI Integration

```python
from fastapi import FastAPI
from sso_apigee_client.fastapi_integration import ApigeeRouter, MOMRAHSSORouter
from sso_apigee_client import ApigeeClient, MOMRAHSSOClient

app = FastAPI()

# Initialize clients
apigee_client = ApigeeClient(
    base_url="http://localhost:3300",
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret"
)

sso_client = MOMRAHSSOClient(
    base_url="http://localhost:3300",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Create and include routers
apigee_router = ApigeeRouter(apigee_client)
sso_router = MOMRAHSSORouter(sso_client)

app.include_router(apigee_router, prefix="/api/apigee", tags=["APIGEE"])
app.include_router(sso_router, prefix="/api/sso", tags=["MOMRAH SSO"])

@app.get("/")
async def root():
    return {"message": "Welcome to your FastAPI app with SSO APIGEE integration"}
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# SSO APIGEE Service Configuration
SSO_APIGEE_SERVICE_URL=http://localhost:3300

# APIGEE Configuration
APIGEE_CONSUMER_KEY=your_apigee_consumer_key
APIGEE_CONSUMER_SECRET=your_apigee_consumer_secret

# MOMRAH SSO Configuration
MOMRAH_CLIENT_ID=your_momrah_client_id
MOMRAH_CLIENT_SECRET=your_momrah_client_secret
```

### Client Configuration

```python
from sso_apigee_client import ApigeeClient, MOMRAHSSOClient

# APIGEE Client with custom configuration
apigee_client = ApigeeClient(
    base_url="http://localhost:3300",
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret",
    timeout=30,  # Request timeout in seconds
    auto_refresh=True  # Auto-refresh tokens (default: True)
)

# MOMRAH SSO Client with custom configuration
sso_client = MOMRAHSSOClient(
    base_url="http://localhost:3300",
    client_id="your_client_id",
    client_secret="your_client_secret",
    timeout=30,  # Request timeout in seconds
    session_secret="your_session_secret"  # Custom session secret
)
```

## API Reference

### ApigeeClient

The `ApigeeClient` provides functionality for interacting with APIGEE API Gateway.

#### Methods

- `get_token(force_refresh=False)`: Get APIGEE access token
- `call_api(method, endpoint, headers=None, data=None)`: Call APIGEE API
- `get_token_status()`: Get token status and expiry information
- `health_check()`: Check APIGEE service health
- `close()`: Close the client and cleanup resources

#### Example

```python
# Get access token
token_response = await apigee_client.get_token()
print(f"Access token: {token_response.access_token}")
print(f"Token type: {token_response.token_type}")
print(f"Expires in: {token_response.expires_in} seconds")

# Call APIGEE API
response = await apigee_client.call_api(
    method="GET",
    endpoint="/api/data",
    headers={"Custom-Header": "value"}
)
print(f"API Response: {response}")

# Check token status
status = await apigee_client.get_token_status()
print(f"Token expires at: {status.expires_at}")
print(f"Token is valid: {status.is_valid}")
```

### MOMRAHSSOClient

The `MOMRAHSSOClient` provides functionality for MOMRAH SSO authentication.

#### Methods

- `get_login_url()`: Get MOMRAH SSO login URL
- `get_current_user()`: Get current authenticated user
- `get_optional_user()`: Get current user (returns None if not authenticated)
- `logout()`: Logout current user
- `refresh_token()`: Refresh user authentication token
- `health_check()`: Check MOMRAH SSO service health

#### Example

```python
# Get login URL
login_url = await sso_client.get_login_url()
print(f"Login URL: {login_url}")

# Get current user
user = await sso_client.get_current_user()
if user:
    print(f"User: {user.name} ({user.email})")
    print(f"User ID: {user.sub}")
    print(f"Roles: {user.roles}")

# Logout user
await sso_client.logout()
print("User logged out successfully")
```

### FastAPI Integration

#### ApigeeRouter

Provides automatic APIGEE token management and API proxying.

**Endpoints:**
- `GET /token` - Get APIGEE access token
- `GET /status` - Get token status and expiry
- `POST /proxy` - Proxy API calls to APIGEE

#### MOMRAHSSORouter

Provides MOMRAH SSO authentication endpoints.

**Endpoints:**
- `GET /login` - Get MOMRAH SSO login URL
- `GET /callback` - Handle OAuth callback
- `GET /user` - Get current authenticated user
- `POST /logout` - Logout current user
- `POST /refresh` - Refresh user token

#### Example

```python
from fastapi import FastAPI, Depends, HTTPException
from sso_apigee_client.fastapi_integration import ApigeeRouter, MOMRAHSSORouter
from sso_apigee_client import ApigeeClient, MOMRAHSSOClient
from sso_apigee_client.models import UserInfo

app = FastAPI()

# Initialize clients
apigee_client = ApigeeClient(
    base_url="http://localhost:3300",
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret"
)

sso_client = MOMRAHSSOClient(
    base_url="http://localhost:3300",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Create routers
apigee_router = ApigeeRouter(apigee_client)
sso_router = MOMRAHSSORouter(sso_client)

# Include routers
app.include_router(apigee_router, prefix="/api/apigee", tags=["APIGEE"])
app.include_router(sso_router, prefix="/api/sso", tags=["MOMRAH SSO"])

# Dependency functions
async def get_current_user() -> UserInfo:
    """Get current authenticated user."""
    user = await sso_client.get_current_user()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# Your application routes
@app.get("/")
async def root():
    return {"message": "Welcome to your FastAPI app"}

@app.get("/profile")
async def get_profile(user: UserInfo = Depends(get_current_user)):
    """Get user profile."""
    return {"user": user.dict()}

@app.get("/apigee-data")
async def get_apigee_data():
    """Get data from APIGEE API."""
    token = await apigee_client.get_token()
    response = await apigee_client.call_api(
        method="GET",
        endpoint="/api/data"
    )
    return {"data": response}
```

## Data Models

### UserInfo

Represents a MOMRAH SSO user.

```python
from sso_apigee_client.models import UserInfo

# UserInfo attributes
user.sub          # User ID
user.name         # Full name
user.email        # Email address
user.given_name   # First name
user.family_name  # Last name
user.roles        # List of user roles
user.groups       # List of user groups
user.organization # Organization name
user.department   # Department name
user.position     # Job position
```

### TokenResponse

Represents an APIGEE token response.

```python
from sso_apigee_client.models import TokenResponse

# TokenResponse attributes
token.access_token     # Access token
token.token_type       # Token type (usually "Bearer")
token.expires_in       # Expiration time in seconds
token.scope           # Token scope
token.refresh_token   # Refresh token (if available)
```

## Error Handling

The SDK provides comprehensive error handling with specific exception types.

### Exception Types

- `ApigeeAuthenticationError`: APIGEE authentication failures
- `MOMRAHSSOError`: MOMRAH SSO authentication failures
- `NetworkError`: Network connectivity issues
- `ConfigurationError`: Configuration problems

### Example

```python
from sso_apigee_client.exceptions import ApigeeAuthenticationError, MOMRAHSSOError

try:
    # Get APIGEE token
    token = await apigee_client.get_token()
    
    # Call APIGEE API
    response = await apigee_client.call_api(
        method="GET",
        endpoint="/api/data"
    )
    
    return response
    
except ApigeeAuthenticationError as e:
    print(f"APIGEE authentication failed: {e}")
    # Handle authentication error
    
except MOMRAHSSOError as e:
    print(f"SSO authentication failed: {e}")
    # Handle SSO error
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

## Advanced Usage

### Custom Headers

```python
# Add custom headers to APIGEE API calls
response = await apigee_client.call_api(
    method="POST",
    endpoint="/api/data",
    headers={
        "Custom-Header": "value",
        "X-Request-ID": "12345"
    },
    data={"key": "value"}
)
```

### Token Management

```python
# Check token status
status = await apigee_client.get_token_status()
if not status.is_valid:
    # Force refresh token
    token = await apigee_client.get_token(force_refresh=True)
    print("Token refreshed")
```

### Session Management

```python
# Get optional user (doesn't raise exception if not authenticated)
user = await sso_client.get_optional_user()
if user:
    print(f"Welcome back, {user.name}")
else:
    print("Please log in")
```

## Testing

### Unit Tests

```python
import pytest
from sso_apigee_client import ApigeeClient, MOMRAHSSOClient

@pytest.mark.asyncio
async def test_apigee_client():
    client = ApigeeClient(
        base_url="http://localhost:3300",
        consumer_key="test_key",
        consumer_secret="test_secret"
    )
    
    # Test token retrieval
    token = await client.get_token()
    assert token.access_token is not None
    
    await client.close()

@pytest.mark.asyncio
async def test_sso_client():
    client = MOMRAHSSOClient(
        base_url="http://localhost:3300",
        client_id="test_client",
        client_secret="test_secret"
    )
    
    # Test login URL generation
    login_url = await client.get_login_url()
    assert "login" in login_url
    
    await client.close()
```

### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from your_app import app

def test_fastapi_integration():
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    
    # Test APIGEE endpoints
    response = client.get("/api/apigee/token")
    assert response.status_code == 200
    
    # Test SSO endpoints
    response = client.get("/api/sso/login")
    assert response.status_code == 200
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install SDK
RUN pip install sso-apigee-client[fastapi]

# Copy application
COPY . .

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

```bash
# Production environment variables
SSO_APIGEE_SERVICE_URL=https://your-sso-service.com
APIGEE_CONSUMER_KEY=your_production_key
APIGEE_CONSUMER_SECRET=your_production_secret
MOMRAH_CLIENT_ID=your_production_client_id
MOMRAH_CLIENT_SECRET=your_production_client_secret
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check APIGEE service
        apigee_health = await apigee_client.health_check()
        
        # Check MOMRAH SSO service
        sso_health = await sso_client.health_check()
        
        return {
            "status": "healthy",
            "apigee": apigee_health,
            "sso": sso_health
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## Best Practices

1. **Environment Variables**: Store sensitive configuration in environment variables
2. **Error Handling**: Always handle authentication and API errors gracefully
3. **Token Management**: Let the SDK handle token refresh automatically
4. **Security**: Use HTTPS in production
5. **Logging**: Implement proper logging for debugging
6. **Health Checks**: Implement health check endpoints
7. **Testing**: Write comprehensive tests for your integration
8. **Monitoring**: Monitor token usage and API calls
9. **Caching**: Use appropriate caching strategies for tokens
10. **Documentation**: Document your integration patterns

## Support

For issues and questions:
- Check the [FastAPI Integration Guide](FASTAPI_INTEGRATION_GUIDE.md)
- Review the SSO APIGEE Service logs
- Contact your system administrator

## License

MIT License - see LICENSE file for details.

## Changelog

### Version 1.1.0
- Added MOMRAH SSO integration
- Enhanced FastAPI integration
- Improved error handling
- Added comprehensive documentation

### Version 1.0.2
- Initial release with APIGEE support
- Basic FastAPI integration
- Token management
- API proxying

---

This SDK provides everything you need to integrate with the SSO APIGEE Service. It handles all the complexity of authentication and API management, allowing you to focus on building your application.