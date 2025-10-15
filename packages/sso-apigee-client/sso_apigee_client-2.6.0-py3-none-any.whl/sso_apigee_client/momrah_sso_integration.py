"""FastAPI integration for MOMRAH SSO authentication."""

from typing import Any, Callable, List, Optional
import os
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from sso_apigee_client.momrah_sso_client import MOMRAHSSOClient

logger = logging.getLogger(__name__)


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


class SSOAuthMiddleware(BaseHTTPMiddleware):
    """
    SSO Authentication Middleware for JWT token validation.
    
    This middleware validates JWT tokens for all protected endpoints.
    Public endpoints are excluded from authentication.
    
    Example:
        from fastapi import FastAPI
        from sso_apigee_client import SSOAuthMiddleware
        
        app = FastAPI()
        
        # Option 1: Pass client instance (legacy, requires manual async init)
        sso_client = MOMRAHSSOClient(
            service_url="http://localhost:3300",
            redirect_uri="https://myapp.com/auth/callback"
        )
        app.add_middleware(SSOAuthMiddleware, sso_client=sso_client)
        
        # Option 2: Pass configuration (recommended)
        app.add_middleware(
            SSOAuthMiddleware,
            service_url="http://localhost:3300",
            redirect_uri="https://myapp.com/auth/callback",
            timeout=30,
            verify_ssl=True
        )
        
        @app.get("/protected")
        async def protected_route(request: Request):
            # User info is available in request.state.user
            return {"user": request.state.user}
    """
    
    def __init__(
        self,
        app,
        sso_client: MOMRAHSSOClient = None,
        service_url: str = None,
        redirect_uri: str = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        public_paths: List[str] = None,
        enabled: bool = None
    ):
        """
        Initialize SSO middleware.
        
        Args:
            app: FastAPI application
            sso_client: MOMRAH SSO client instance (legacy mode)
            service_url: SSO service URL (new mode)
            redirect_uri: Application redirect URI (new mode)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            public_paths: List of paths that don't require authentication
            enabled: Override SSO_AUTH_ENABLED from environment
        """
        super().__init__(app)
        
        # Support both legacy and new initialization patterns
        if sso_client is not None:
            # Legacy mode: use provided client
            self.sso_client = sso_client
            self._client_initialized = True
            logger.info("SSO Auth Middleware initialized in legacy mode")
        elif service_url and redirect_uri:
            # New mode: create client internally
            self.sso_client = MOMRAHSSOClient(
                service_url=service_url,
                redirect_uri=redirect_uri,
                timeout=timeout,
                verify_ssl=verify_ssl
            )
            self._client_initialized = False
            logger.info("SSO Auth Middleware initialized in new mode")
        else:
            raise ValueError(
                "Either 'sso_client' or both 'service_url' and 'redirect_uri' must be provided"
            )
        
        # Default public paths (no authentication required)
        self.public_paths = public_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/callback",
            "/auth/validate",
            "/auth/refresh",
            "/auth/logout",
        ]
        
        # Check if SSO is enabled
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = os.getenv("SSO_AUTH_ENABLED", "true").lower() == "true"
        
        logger.info(f"SSO Auth Middleware initialized (enabled: {self.enabled})")
        if self.enabled:
            logger.info(f"Public paths (no auth required): {self.public_paths}")
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and validate JWT token if required.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from next middleware/endpoint or error response
        """
        # Skip authentication if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Validate JWT token
        try:
            user_info = await self._validate_token(request)
            
            # Add user info to request state
            request.state.user = user_info
            
            # Continue to endpoint
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Return authentication error
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authentication error"}
            )
    
    def _is_public_path(self, path: str) -> bool:
        """
        Check if path is public (doesn't require authentication).
        
        Args:
            path: Request path
            
        Returns:
            True if path is public, False otherwise
        """
        # Exact match
        if path in self.public_paths:
            return True
        
        # Prefix match (for paths like /auth/*)
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return True
        
        return False
    
    async def _validate_token(self, request: Request) -> dict:
        """
        Extract and validate JWT token from request.
        
        Args:
            request: Incoming HTTP request
            
        Returns:
            User information from validated token
            
        Raises:
            HTTPException: If token is missing or invalid
        """
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check Bearer format
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication format. Use: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token
        token = auth_header.replace("Bearer ", "").strip()
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Empty authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token using SSO client with proper async context management
        try:
            # Use async context manager for proper client initialization
            async with self.sso_client as client:
                user_info = await client.validate_token(token)
            
            # Add authenticated flag
            user_info["authenticated"] = True
            
            logger.info(f"User authenticated: {user_info.get('sub', 'unknown')}")
            
            return user_info
            
        except HTTPException:
            # Re-raise HTTPException from SSO client
            raise
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )


def add_public_path(middleware: SSOAuthMiddleware, path: str):
    """
    Add a path to the public paths list (helper function).
    
    Args:
        middleware: SSOAuthMiddleware instance
        path: Path to add to public paths
    """
    if path not in middleware.public_paths:
        middleware.public_paths.append(path)
        logger.info(f"Added public path: {path}")
