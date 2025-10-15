"""
SSO APIGEE Client SDK

A Python client library for interacting with APIGEE and MOMRAH SSO services.

This SDK provides:
- APIGEE OAuth2 token management and API proxying
- MOMRAH SSO authentication and user management
- FastAPI integration for both services

Example (APIGEE):
    from sso_apigee_client import ApigeeClient
    
    async with ApigeeClient("http://localhost:3300") as client:
        # Get APIGEE token
        token = await client.get_token()
        
        # Make API call through APIGEE
        data = await client.call_api("GET", "/api/v1/data")

Example (MOMRAH SSO):
    from sso_apigee_client import MOMRAHSSOClient
    
    async with MOMRAHSSOClient("http://localhost:3300") as client:
        # Get login URL
        login = await client.get_login_url()
        
        # Get current user
        user = await client.get_current_user()
"""

from sso_apigee_client.apigee_client import ApigeeClient
from sso_apigee_client.exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    SSOApigeeError,
)
from sso_apigee_client.models import TokenStatus
from sso_apigee_client.momrah_sso_client import MOMRAHSSOClient

__version__ = "1.1.0"

# Core exports
__all__ = [
    # APIGEE
    "ApigeeClient",
    # MOMRAH SSO
    "MOMRAHSSOClient",
    # Exceptions
    "SSOApigeeError",
    "AuthenticationError",
    "APIError",
    "ConnectionError",
    # Models
    "TokenStatus",
]

# FastAPI integration is optional - only import if FastAPI is installed
try:
    from sso_apigee_client.fastapi_integration import (
        ApigeeRouter,
        create_apigee_dependency,
    )
    from sso_apigee_client.momrah_sso_integration import (
        MOMRAHSSORouter,
        MOMRAHSSOSettings,
        SSOAuthMiddleware,
        create_sso_dependency,
        get_current_user,
        get_optional_user,
        add_public_path,
    )
    __all__.extend([
        # APIGEE FastAPI
        "ApigeeRouter",
        "create_apigee_dependency",
        # MOMRAH SSO FastAPI
        "MOMRAHSSORouter",
        "MOMRAHSSOSettings",
        "SSOAuthMiddleware",
        "create_sso_dependency",
        "get_current_user",
        "get_optional_user",
        "add_public_path",
    ])
except ImportError:
    # FastAPI not installed - integration not available
    pass
