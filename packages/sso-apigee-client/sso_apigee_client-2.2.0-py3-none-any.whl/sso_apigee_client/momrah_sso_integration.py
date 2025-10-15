"""FastAPI integration for MOMRAH SSO authentication."""

from typing import Any, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from sso_apigee_client.momrah_sso_client import MOMRAHSSOClient


class MOMRAHSSOSettings(BaseModel):
    """
    MOMRAH SSO settings for FastAPI integration.
    
    This allows each application to provide its own configuration
    without relying on environment variables.
    
    Example:
        from sso_apigee_client import MOMRAHSSOSettings
        
        # Option 1: Use service URL (service handles SSO)
        settings = MOMRAHSSOSettings(
            service_url="http://localhost:3300",
            enabled=True,
        )
        
        # Option 2: Direct SSO configuration (bypass service)
        settings = MOMRAHSSOSettings(
            service_url="http://localhost:3300",
            enabled=True,
            # Optional: Override with app-specific settings
            client_id="your_app_client_id",
            client_secret="your_app_client_secret",
            redirect_uri="https://yourapp.com/auth/callback",
        )
    """
    
    service_url: str
    enabled: bool = True
    timeout: float = 30.0
    verify_ssl: bool = True
    
    # Optional: App-specific MOMRAH SSO configuration
    # If provided, these will be passed to the service
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    post_logout_redirect_uri: Optional[str] = None
    scopes: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        frozen = True


class MOMRAHSSORouter:
    """
    FastAPI router for MOMRAH SSO authentication.
    
    This router provides pre-configured endpoints for SSO authentication
    that can be easily integrated into any FastAPI application.
    
    Example:
        from fastapi import FastAPI
        from sso_apigee_client import MOMRAHSSORouter, MOMRAHSSOSettings
        
        app = FastAPI()
        
        settings = MOMRAHSSOSettings(service_url="http://localhost:3300")
        sso_router = MOMRAHSSORouter(settings)
        
        app.include_router(sso_router.get_router())
        
        # Now you have /auth/login, /auth/callback, /auth/user, etc.
    """
    
    def __init__(
        self,
        settings: MOMRAHSSOSettings,
        prefix: str = "",
        tags: Optional[list] = None,
    ):
        """
        Initialize MOMRAH SSO router.
        
        Args:
            settings: MOMRAH SSO settings
            prefix: Router prefix (default: "")
            tags: OpenAPI tags (default: ["Authentication"])
        """
        self.settings = settings
        self.prefix = prefix
        self.tags = tags or ["Authentication"]
        self._client: Optional[MOMRAHSSOClient] = None
    
    @property
    def client(self) -> MOMRAHSSOClient:
        """Get or create SSO client."""
        if self._client is None:
            if not self.settings.redirect_uri:
                raise ValueError("redirect_uri must be provided in MOMRAHSSOSettings")
            self._client = MOMRAHSSOClient(
                service_url=self.settings.service_url,
                redirect_uri=self.settings.redirect_uri,
                timeout=self.settings.timeout,
                verify_ssl=self.settings.verify_ssl,
            )
        return self._client
    
    def get_router(self) -> APIRouter:
        """
        Get configured FastAPI router.
        
        Returns:
            APIRouter with SSO endpoints
        """
        router = APIRouter(prefix=self.prefix, tags=self.tags)
        
        @router.get("/auth/login")
        async def login(redirect_to: Optional[str] = None):
            """Get SSO login URL."""
            async with self.client as client:
                return await client.get_login_url(redirect_to)
        
        @router.get("/auth/user")
        async def get_user(request: Request):
            """Get current authenticated user from JWT token."""
            # Extract JWT from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid token")
            
            access_token = auth_header.split(" ")[1]
            
            async with self.client as client:
                return await client.get_user(access_token)
        
        @router.post("/auth/logout")
        async def logout():
            """Get MOMRAH SSO logout URL."""
            async with self.client as client:
                return await client.get_logout_url()
        
        @router.post("/auth/refresh")
        async def refresh(request: Request):
            """Refresh access token using refresh token."""
            # Parse request body to get refresh token
            body = await request.json()
            refresh_token = body.get("refresh_token")
            
            if not refresh_token:
                raise HTTPException(status_code=400, detail="Refresh token required")
            
            async with self.client as client:
                return await client.refresh_access_token(refresh_token)
        
        return router


def create_sso_dependency(sso_client: MOMRAHSSOClient) -> Callable:
    """
    Create a FastAPI dependency that provides MOMRAH SSO client.
    
    This allows you to inject the SSO client into your endpoints
    for manual control when needed.
    
    Example:
        from fastapi import Depends, FastAPI
        from sso_apigee_client import MOMRAHSSOClient
        from sso_apigee_client.momrah_sso_integration import create_sso_dependency
        
        app = FastAPI()
        sso_client = MOMRAHSSOClient("http://localhost:3300", "https://myapp.com/auth/callback")
        get_sso = create_sso_dependency(sso_client)
        
        @app.get("/profile")
        async def profile(sso: MOMRAHSSOClient = Depends(get_sso)):
            user = await sso.get_current_user()
            return {"profile": user}
    
    Args:
        sso_client: MOMRAH SSO client instance
        
    Returns:
        Dependency function
    """
    async def get_sso_client() -> MOMRAHSSOClient:
        """Dependency that returns MOMRAH SSO client."""
        return sso_client
    
    return get_sso_client


def get_jwt_token(request: Request) -> str:
    """
    Extract JWT token from Authorization header.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_header.split(" ")[1]


def get_current_user(sso_client: MOMRAHSSOClient) -> Callable:
    """
    Create a dependency that returns the current authenticated user from JWT.
    
    Example:
        from fastapi import Depends, FastAPI
        from sso_apigee_client import MOMRAHSSOClient
        from sso_apigee_client.momrah_sso_integration import get_current_user
        
        app = FastAPI()
        sso_client = MOMRAHSSOClient("http://localhost:3300", "https://myapp.com/auth/callback")
        current_user = get_current_user(sso_client)
        
        @app.get("/protected")
        async def protected(user = Depends(current_user)):
            return {"message": f"Hello {user['user']['full_name']}"}
    
    Args:
        sso_client: MOMRAH SSO client instance
        
    Returns:
        Dependency function that returns current user
    """
    async def _get_current_user(token: str = Depends(get_jwt_token)) -> dict:
        """Get current authenticated user from JWT token."""
        async with sso_client as client:
            try:
                return await client.validate_token(token)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    
    return _get_current_user


def get_optional_user(sso_client: MOMRAHSSOClient) -> Callable:
    """
    Create a dependency that returns the current user or None from JWT.
    
    Example:
        from fastapi import Depends, FastAPI
        from sso_apigee_client import MOMRAHSSOClient
        from sso_apigee_client.momrah_sso_integration import get_optional_user
        
        app = FastAPI()
        sso_client = MOMRAHSSOClient("http://localhost:3300", "https://myapp.com/auth/callback")
        optional_user = get_optional_user(sso_client)
        
        @app.get("/public")
        async def public(user = Depends(optional_user)):
            if user:
                return {"message": f"Hello {user['user']['full_name']}"}
            return {"message": "Hello guest"}
    
    Args:
        sso_client: MOMRAH SSO client instance
        
    Returns:
        Dependency function that returns current user or None
    """
    async def _get_optional_user(request: Request) -> Optional[dict]:
        """Get current authenticated user (optional) from JWT token."""
        # Try to extract JWT from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        access_token = auth_header.split(" ")[1]
        
        async with sso_client as client:
            try:
                return await client.validate_token(access_token)
            except Exception:
                return None
    
    return _get_optional_user
