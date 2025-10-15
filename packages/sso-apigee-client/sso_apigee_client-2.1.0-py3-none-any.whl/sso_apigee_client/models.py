from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TokenInfo(BaseModel):
    
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: Optional[int] = Field(default=None, description="Token expiry in seconds")


class User(BaseModel):
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Create User from dictionary.
        
        Args:
            data: User data dictionary
            
        Returns:
            User instance
        """
        return cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            full_name=data["full_name"],
            role=data["role"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
        )


class APIResponse(BaseModel):
    """Generic API response model."""
    
    status_code: int = Field(..., description="HTTP status code")
    data: Dict[str, Any] = Field(..., description="Response data")
    headers: Dict[str, str] = Field(..., description="Response headers")


class TokenStatus(BaseModel):
    """Token status information."""
    
    token_cached: bool = Field(..., description="Whether token is cached")
    is_valid: Optional[bool] = Field(default=None, description="Whether token is valid")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiration time")
    seconds_until_expiry: Optional[int] = Field(default=None, description="Seconds until expiry")
    token_type: Optional[str] = Field(default=None, description="Token type")
