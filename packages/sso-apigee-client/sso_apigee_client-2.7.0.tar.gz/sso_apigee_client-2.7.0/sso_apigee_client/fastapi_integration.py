from typing import Any, Callable, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.routing import APIRoute

from sso_apigee_client.apigee_client import ApigeeClient
from sso_apigee_client.exceptions import APIError, AuthenticationError


class ApigeeRoute(APIRoute):
    """
    Custom APIRoute that automatically proxies requests through APIGEE.
    
    This route class intercepts all requests and forwards them to APIGEE
    with automatic authentication handling.
    """
    
    def __init__(self, *args: Any, apigee_client: ApigeeClient, **kwargs: Any):
        """
        Initialize APIGEE route.
        
        Args:
            apigee_client: APIGEE client instance
            *args: APIRoute arguments
            **kwargs: APIRoute keyword arguments
        """
        self.apigee_client = apigee_client
        super().__init__(*args, **kwargs)


class ApigeeRouter(APIRouter):
    """
    FastAPI Router wrapper that automatically handles APIGEE authentication.
    
    This router wraps all endpoints to automatically proxy requests through APIGEE,
    eliminating the need to manually call `call_api()` in each endpoint.
    
    Example:
        from sso_apigee_client import ApigeeClient
        from sso_apigee_client.fastapi_integration import ApigeeRouter
        
        apigee_client = ApigeeClient("http://localhost:8000")
        router = ApigeeRouter(apigee_client=apigee_client, prefix="/api")
        
        @router.get("/users")
        async def get_users():
            # Automatically proxied through APIGEE!
            # No need to call apigee_client.call_api()
            return {"message": "This will be proxied"}
    """
    
    def __init__(
        self,
        apigee_client: ApigeeClient,
        apigee_base_path: str = "",
        auto_proxy: bool = True,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initialize APIGEE Router.
        
        Args:
            apigee_client: APIGEE client instance
            apigee_base_path: Base path for APIGEE endpoints (e.g., "/api/v1")
            auto_proxy: If True, automatically proxy all requests through APIGEE
            *args: APIRouter arguments
            **kwargs: APIRouter keyword arguments
        """
        self.apigee_client = apigee_client
        self.apigee_base_path = apigee_base_path.rstrip("/")
        self.auto_proxy = auto_proxy
        
        super().__init__(*args, **kwargs)
    
    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *args: Any,
        apigee_endpoint: Optional[str] = None,
        skip_apigee: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Add API route with APIGEE proxying.
        
        Args:
            path: Route path
            endpoint: Endpoint function
            apigee_endpoint: Custom APIGEE endpoint (if different from path)
            skip_apigee: Skip APIGEE proxying for this route
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        if skip_apigee or not self.auto_proxy:
            super().add_api_route(path, endpoint, *args, **kwargs)
            return
        
        if apigee_endpoint is None:
            apigee_endpoint = f"{self.apigee_base_path}{path}"
        
        methods = kwargs.get("methods", ["GET"])
        if isinstance(methods, str):
            methods = [methods]
        
        async def apigee_wrapped_endpoint(request: Request, **path_params: Any) -> Any:
            try:
                body = None
                if request.method in ["POST", "PUT", "PATCH"]:
                    try:
                        body = await request.json()
                    except Exception:
                        body = None
                
                query_params = dict(request.query_params) if request.query_params else None
                
                formatted_endpoint = apigee_endpoint
                for key, value in path_params.items():
                    formatted_endpoint = formatted_endpoint.replace(f"{{{key}}}", str(value))
                
                result = await self.apigee_client.call_api(
                    method=request.method,
                    endpoint=formatted_endpoint,
                    headers=dict(request.headers),
                    body=body,
                    query_params=query_params,
                )
                
                return result
                
            except AuthenticationError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"APIGEE authentication failed: {e.message}",
                )
            except APIError as e:
                raise HTTPException(
                    status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"APIGEE API error: {e.message}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error: {str(e)}",
                )
        
        super().add_api_route(
            path,
            apigee_wrapped_endpoint,
            *args,
            **kwargs,
        )


def create_apigee_dependency(apigee_client: ApigeeClient) -> Callable:
    """
    Create a FastAPI dependency that provides APIGEE client.
    
    This allows you to inject the APIGEE client into your endpoints
    for manual control when needed.
    
    Example:
        from fastapi import Depends
        from sso_apigee_client import ApigeeClient
        from sso_apigee_client.fastapi_integration import create_apigee_dependency
        
        apigee_client = ApigeeClient("http://localhost:8000")
        get_apigee = create_apigee_dependency(apigee_client)
        
        @app.get("/custom")
        async def custom_endpoint(apigee: ApigeeClient = Depends(get_apigee)):
            # Manual control over APIGEE calls
            data = await apigee.call_api("GET", "/api/v1/data")
            return data
    
    Args:
        apigee_client: APIGEE client instance
        
    Returns:
        Dependency function
    """
    async def get_apigee_client() -> ApigeeClient:
        """Dependency that returns APIGEE client."""
        return apigee_client
    
    return get_apigee_client
