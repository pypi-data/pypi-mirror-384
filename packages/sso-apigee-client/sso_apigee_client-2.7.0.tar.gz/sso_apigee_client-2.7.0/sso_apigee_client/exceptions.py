"""Custom exceptions for SSO APIGEE Client."""

from typing import Any, Dict, Optional


class SSOApigeeError(Exception):
    """Base exception for SSO APIGEE Client."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize SSO APIGEE error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(SSOApigeeError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, status_code=401, details=details)


class APIError(SSOApigeeError):
    """Raised when API call fails."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message, status_code=status_code, details=details)


class ConnectionError(SSOApigeeError):
    """Raised when connection to service fails."""
    
    def __init__(
        self,
        message: str = "Failed to connect to SSO APIGEE Service",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize connection error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, status_code=503, details=details)
