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
        
        async with MOMRAHSSOClient("http://localhost:3300") as client:
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
        redirect_uri: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize MOMRAH SSO client.
        
        Args:
            service_url: Base URL of the SSO service
            redirect_uri: OAuth2 redirect URI for the client application
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.service_url = service_url.rstrip("/")
        self.redirect_uri = redirect_uri
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
        params = {"redirect_uri": self.redirect_uri}
        if redirect_to:
            params["redirect_to"] = redirect_to
        
        return await self._request("GET", "/auth/login", params=params)
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for JWT tokens.
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter for CSRF validation (PKCE verifier handled automatically)
            
        Returns:
            JWT authentication response with tokens and user info
            
        Example:
            response = await client.exchange_code_for_token(code, state)
            access_token = response['access_token']
            user_info = response['user']
        """
        return await self._request(
            "GET",
            "/auth/callback",
            params={"code": code, "state": state}
        )
    
    async def validate_token(self, access_token: str) -> Dict[str, Any]:
        """
        Validate JWT token and get user information.
        
        Args:
            access_token: JWT access token
            
        Returns:
            User information from validated token
            
        Example:
            user_info = await client.validate_token(access_token)
            print(f"Hello, {user_info['user']['full_name']}")
        """
        return await self._request(
            "POST",
            "/auth/validate",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    async def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from JWT token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            User information from JWT token
            
        Example:
            user_info = await client.get_user(access_token)
            print(f"Hello, {user_info['user']['full_name']}")
        """
        return await self._request(
            "GET",
            "/auth/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New JWT authentication response
            
        Example:
            response = await client.refresh_access_token(refresh_token)
            new_access_token = response['access_token']
        """
        return await self._request(
            "POST",
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
    
    async def get_logout_url(self) -> Dict[str, Any]:
        """
        Get MOMRAH SSO logout URL.
        
        Returns:
            Logout response with redirect URL
            
        Example:
            response = await client.get_logout_url()
            print(f"Logout URL: {response['redirect_url']}")
        """
        return await self._request("POST", "/auth/logout")
    
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
