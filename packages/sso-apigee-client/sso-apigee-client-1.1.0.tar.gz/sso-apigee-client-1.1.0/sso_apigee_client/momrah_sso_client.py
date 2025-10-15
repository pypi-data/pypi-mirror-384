"""MOMRAH SSO Client for Python applications."""

from typing import Any, Dict, Optional

import httpx

from sso_apigee_client.exceptions import APIError, AuthenticationError, ConnectionError


class MOMRAHSSOClient:
    """
    Client for MOMRAH SSO authentication service.
    
    This client provides methods to interact with the MOMRAH SSO service
    for user authentication, session management, and user information retrieval.
    
    Example:
        from sso_apigee_client import MOMRAHSSOClient
        
        async with MOMRAHSSOClient("http://localhost:8000") as client:
            # Get login URL
            login_response = await client.get_login_url()
            print(f"Login at: {login_response['authorization_url']}")
            
            # After OAuth callback, get user info
            user = await client.get_current_user()
            print(f"Hello, {user['full_name']}")
    """
    
    def __init__(
        self,
        service_url: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize MOMRAH SSO client.
        
        Args:
            service_url: Base URL of the SSO service
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.service_url = service_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self) -> "MOMRAHSSOClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client instance."""
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with MOMRAHSSOClient(...)' "
                "or call __aenter__() first."
            )
        return self._client
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to SSO service.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
            APIError: If API returns an error
        """
        url = f"{self.service_url}{endpoint}"
        
        try:
            response = await self.client.request(method, url, **kwargs)
            
            # Handle authentication errors
            if response.status_code == 401:
                error_detail = "Authentication required"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except Exception:
                    pass
                
                raise AuthenticationError(
                    message=error_detail,
                    details={"status_code": 401},
                )
            
            # Handle other errors
            if response.status_code >= 400:
                error_detail = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except Exception:
                    error_detail = response.text or error_detail
                
                raise APIError(
                    message=error_detail,
                    status_code=response.status_code,
                    details={"url": url},
                )
            
            # Parse response
            try:
                return response.json()
            except Exception:
                return {"raw_response": response.text}
        
        except httpx.RequestError as e:
            raise ConnectionError(
                message=f"Connection failed: {str(e)}",
                details={"url": url},
            )
    
    async def get_login_url(self, redirect_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Get MOMRAH SSO login URL.
        
        Args:
            redirect_to: Optional URL to redirect to after login
            
        Returns:
            Dictionary with 'authorization_url' and 'state'
            
        Example:
            response = await client.get_login_url()
            print(f"Login at: {response['authorization_url']}")
        """
        params = {}
        if redirect_to:
            params["redirect_to"] = redirect_to
        
        return await self._request("GET", "/auth/login", params=params)
    
    async def get_current_user(self) -> Dict[str, Any]:
        """
        Get current authenticated user information.
        
        Returns:
            User information dictionary
            
        Raises:
            AuthenticationError: If user is not authenticated
            
        Example:
            user = await client.get_current_user()
            print(f"Hello, {user['user']['full_name']}")
        """
        return await self._request("GET", "/auth/user")
    
    async def get_optional_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user information (optional).
        
        Returns:
            User information dictionary if authenticated, None otherwise
            
        Example:
            user = await client.get_optional_user()
            if user:
                print(f"Hello, {user['full_name']}")
            else:
                print("Not logged in")
        """
        try:
            return await self._request("GET", "/auth/user/optional")
        except AuthenticationError:
            return None
    
    async def logout(self) -> Dict[str, Any]:
        """
        Logout current user.
        
        Returns:
            Logout response with message and redirect URL
            
        Example:
            response = await client.logout()
            print(response['message'])
        """
        return await self._request("POST", "/auth/logout")
    
    async def refresh_token(self) -> Dict[str, Any]:
        """
        Refresh access token.
        
        Returns:
            Updated user information
            
        Example:
            user_info = await client.refresh_token()
            print(f"Token refreshed for: {user_info['user']['full_name']}")
        """
        return await self._request("POST", "/auth/refresh")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check service health.
        
        Returns:
            Health status dictionary
            
        Example:
            health = await client.health_check()
            print(f"Service status: {health['status']}")
        """
        return await self._request("GET", "/health")
