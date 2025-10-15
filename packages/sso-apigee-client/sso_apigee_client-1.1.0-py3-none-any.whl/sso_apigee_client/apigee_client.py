"""Main client for APIGEE Service - APIGEE functionality only."""

import logging
from typing import Any, Dict, Optional

import httpx

from sso_apigee_client.exceptions import APIError, AuthenticationError, ConnectionError
from sso_apigee_client.models import TokenStatus

logger = logging.getLogger(__name__)


class ApigeeClient:
    """
    Client for interacting with APIGEE Service.
    
    This client provides APIGEE-specific functionality:
    - Getting APIGEE OAuth2 access tokens
    - Making authenticated API calls via APIGEE proxy
    - Token status management
    
    Note: This does NOT handle user authentication (SSO).
    User authentication will be in a separate SSO SDK.
    
    Example:
        >>> client = ApigeeClient("http://localhost:8000")
        >>> token = await client.get_token()
        >>> data = await client.call_api("GET", "/api/v1/data")
    """
    
    def __init__(
        self,
        service_url: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize APIGEE Client.
        
        Args:
            service_url: URL of the APIGEE Service
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.service_url = service_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.AsyncClient] = None
        self._cached_token: Optional[str] = None
        
        logger.info(f"Initialized APIGEE Client for {self.service_url}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                verify=self.verify_ssl,
            )
        return self._client
    
    async def get_token(self, force_refresh: bool = False) -> str:
        """
        Get APIGEE OAuth2 access token.
        
        Args:
            force_refresh: Force token refresh even if cached
            
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If token fetch fails
            ConnectionError: If service is unreachable
        """
        if self._cached_token and not force_refresh:
            logger.debug("Using cached APIGEE token")
            return self._cached_token
        
        client = await self._get_client()
        
        try:
            logger.info("Fetching new APIGEE token")
            response = await client.post(
                f"{self.service_url}/apigee/token",
                params={"force_refresh": force_refresh},
            )
            response.raise_for_status()
            
            data = response.json()
            self._cached_token = data["access_token"]
            
            logger.info("APIGEE token fetched successfully")
            return self._cached_token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"APIGEE token fetch failed: {e.response.status_code}")
            raise AuthenticationError(
                message="Failed to get APIGEE access token",
                details={"status_code": e.response.status_code, "response": e.response.text},
            )
        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                message="Failed to connect to APIGEE service",
                details={"error": str(e)},
            )
    
    async def call_api(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call API via APIGEE proxy with automatic authentication.
        
        This method automatically handles APIGEE token management
        and forwards your request through APIGEE gateway.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path
            headers: Additional request headers
            body: Request body
            query_params: URL query parameters
            
        Returns:
            API response data
            
        Raises:
            APIError: If API call fails
            ConnectionError: If service is unreachable
        """
        client = await self._get_client()
        
        try:
            logger.debug(f"Calling APIGEE API: {method} {endpoint}")
            
            response = await client.post(
                f"{self.service_url}/apigee/proxy",
                json={
                    "method": method,
                    "endpoint": endpoint,
                    "headers": headers,
                    "body": body,
                    "query_params": query_params,
                },
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"APIGEE API call successful: {result['status_code']}")
            
            return result["data"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"APIGEE API call failed: {e.response.status_code}")
            raise APIError(
                message=f"APIGEE API call failed: {method} {endpoint}",
                status_code=e.response.status_code,
                details={"response": e.response.text},
            )
        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(
                message="Failed to connect to APIGEE service",
                details={"error": str(e)},
            )
    
    async def get_token_status(self) -> TokenStatus:
        """
        Get current APIGEE token status.
        
        Returns:
            Token status information including validity and expiry
        """
        client = await self._get_client()
        response = await client.get(f"{self.service_url}/apigee/token/status")
        response.raise_for_status()
        data = response.json()
        
        return TokenStatus(**data)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check APIGEE service health.
        
        Returns:
            Health status information
        """
        client = await self._get_client()
        response = await client.get(f"{self.service_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("APIGEE client closed")
    
    async def __aenter__(self) -> "ApigeeClient":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
