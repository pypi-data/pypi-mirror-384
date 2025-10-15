# SSO APIGEE Client SDK

A Python client library for interacting with APIGEE Service, providing seamless OAuth2 token management and API proxying capabilities.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Features

✨ **Easy to Use** - Simple, intuitive API for APIGEE integration  
🔐 **Automatic Token Management** - Built-in OAuth2 token caching and refresh  
🚀 **FastAPI Integration** - Seamless integration with FastAPI applications  
⚡ **Async/Await Support** - Modern async Python for high performance  
🛡️ **Type Hints** - Full type annotations for better IDE support  
🔧 **Flexible** - Works standalone or integrated with web frameworks  

## Installation

```bash
pip install sso-apigee-client
```

### With FastAPI Support

```bash
pip install sso-apigee-client[fastapi]
```

## Quick Start

### Standalone Usage

```python
import asyncio
from sso_apigee_client import ApigeeClient

async def main():
    async with ApigeeClient("http://localhost:8000") as client:
        # Get APIGEE token
        token = await client.get_token()
        
        # Call API through APIGEE
        users = await client.call_api("GET", "/api/v1/users")
        print(users)

asyncio.run(main())
```

### FastAPI Integration

```python
from fastapi import FastAPI
from sso_apigee_client import ApigeeClient
from sso_apigee_client.fastapi_integration import ApigeeRouter

app = FastAPI()
apigee_client = ApigeeClient("http://localhost:8000")

# Create router with auto-proxy
router = ApigeeRouter(
    apigee_client=apigee_client,
    apigee_base_path="/api/v1",
    prefix="/api"
)

@router.get("/users")
async def get_users():
    """Automatically proxied to APIGEE GET /api/v1/users"""
    pass

app.include_router(router)
```

## Core Features

### 1. Token Management

```python
# Get token (cached automatically)
token = await client.get_token()

# Force refresh
token = await client.get_token(force_refresh=True)

# Check token status
status = await client.get_token_status()
print(f"Valid: {status.is_valid}")
print(f"Expires in: {status.seconds_until_expiry} seconds")
```

### 2. API Calls

```python
# GET request
users = await client.call_api("GET", "/api/v1/users")

# POST request
new_user = await client.call_api(
    "POST",
    "/api/v1/users",
    body={"name": "John Doe", "email": "john@example.com"}
)

# With query parameters
filtered = await client.call_api(
    "GET",
    "/api/v1/users",
    query_params={"role": "admin", "limit": 10}
)

# With custom headers
data = await client.call_api(
    "GET",
    "/api/v1/data",
    headers={"X-Custom-Header": "value"}
)
```

### 3. FastAPI Auto-Proxy Router

```python
from sso_apigee_client.fastapi_integration import ApigeeRouter

router = ApigeeRouter(
    apigee_client=apigee_client,
    apigee_base_path="/api/v1",
    prefix="/api"
)

@router.get("/users")
async def get_users():
    # Automatically proxied to APIGEE: GET /api/v1/users
    pass

@router.post("/users")
async def create_user():
    # Automatically proxied to APIGEE: POST /api/v1/users
    pass

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    # Automatically proxied to APIGEE: GET /api/v1/users/{user_id}
    pass
```

### 4. Dependency Injection

```python
from fastapi import Depends
from sso_apigee_client.fastapi_integration import create_apigee_dependency

get_apigee = create_apigee_dependency(apigee_client)

@app.get("/custom")
async def custom_endpoint(apigee: ApigeeClient = Depends(get_apigee)):
    # Manual control over APIGEE calls
    users = await apigee.call_api("GET", "/api/v1/users")
    roles = await apigee.call_api("GET", "/api/v1/roles")
    return {"users": users, "roles": roles}
```

## Error Handling

```python
from sso_apigee_client import (
    ApigeeClient,
    AuthenticationError,
    APIError,
    ConnectionError
)

async def safe_call():
    try:
        async with ApigeeClient("http://localhost:8000") as client:
            result = await client.call_api("GET", "/api/v1/users")
            return result
            
    except AuthenticationError as e:
        print(f"Auth failed: {e.message}")
        
    except APIError as e:
        print(f"API error: {e.message} (status: {e.status_code})")
        
    except ConnectionError as e:
        print(f"Connection failed: {e.message}")
```

## Configuration

### Client Options

```python
client = ApigeeClient(
    service_url="http://localhost:8000",  # Required: APIGEE service URL
    timeout=30.0,                          # Optional: Request timeout (seconds)
    verify_ssl=True                        # Optional: SSL verification
)
```

### Environment Variables

```python
import os

client = ApigeeClient(
    service_url=os.getenv("APIGEE_SERVICE_URL"),
    timeout=float(os.getenv("APIGEE_TIMEOUT", "30.0")),
    verify_ssl=os.getenv("APIGEE_VERIFY_SSL", "true").lower() == "true"
)
```

## API Reference

### ApigeeClient

#### Methods

- **`get_token(force_refresh=False)`** - Get APIGEE OAuth2 token
- **`call_api(method, endpoint, headers=None, body=None, query_params=None)`** - Call API via APIGEE proxy
- **`get_token_status()`** - Get current token status
- **`health_check()`** - Check service health
- **`close()`** - Close client and cleanup resources

### ApigeeRouter

FastAPI router with automatic APIGEE proxying.

#### Constructor

```python
ApigeeRouter(
    apigee_client: ApigeeClient,
    apigee_base_path: str = "",
    auto_proxy: bool = True,
    **kwargs  # Standard APIRouter arguments
)
```

### create_apigee_dependency

Create FastAPI dependency for APIGEE client injection.

```python
get_apigee = create_apigee_dependency(apigee_client)
```

## Examples

### Example 1: Simple Script

```python
import asyncio
from sso_apigee_client import ApigeeClient

async def main():
    async with ApigeeClient("http://localhost:8000") as client:
        # List users
        users = await client.call_api("GET", "/api/v1/users")
        
        # Create user
        new_user = await client.call_api(
            "POST",
            "/api/v1/users",
            body={"name": "Alice", "email": "alice@example.com"}
        )
        
        print(f"Created: {new_user}")

asyncio.run(main())
```

### Example 2: FastAPI App

```python
from fastapi import FastAPI, Depends
from sso_apigee_client import ApigeeClient
from sso_apigee_client.fastapi_integration import (
    ApigeeRouter,
    create_apigee_dependency
)

app = FastAPI()
apigee_client = ApigeeClient("http://localhost:8000")

# Auto-proxy router
api_router = ApigeeRouter(
    apigee_client=apigee_client,
    apigee_base_path="/api/v1",
    prefix="/api"
)

@api_router.get("/users")
async def list_users():
    pass  # Auto-proxied

@api_router.post("/users")
async def create_user():
    pass  # Auto-proxied

app.include_router(api_router)

# Manual control
get_apigee = create_apigee_dependency(apigee_client)

@app.get("/stats")
async def stats(apigee: ApigeeClient = Depends(get_apigee)):
    users = await apigee.call_api("GET", "/api/v1/users")
    return {"total": len(users)}
```

## Requirements

- Python 3.11+
- httpx >= 0.25.0
- pydantic >= 2.5.0
- fastapi >= 0.104.0 (optional, for FastAPI integration)

## Development

### Install for Development

```bash
git clone <repository-url>
cd sdk/python
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Build Package

```bash
python -m build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See [DEVELOPER_GUIDE.md](../../DEVELOPER_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/yourorg/sso-apigee-service/issues)
- **Email**: dev@yourorg.com

## Changelog

### Version 1.0.2
- Fixed import paths for better compatibility
- Made FastAPI integration optional
- Improved error handling

### Version 1.0.1
- Fixed module import issues
- Updated documentation

### Version 1.0.0
- Initial release
- Core APIGEE client functionality
- FastAPI integration
- Token management
- Auto-proxy router
