"""
User and authentication schemas
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration for RBAC"""
    ADMIN = "admin"
    ANALYST_TIER1 = "analyst_tier1"
    ANALYST_TIER2 = "analyst_tier2"
    READONLY = "readonly"
    API_SERVICE = "api_service"


class UserCreateRequest(BaseModel):
    """Create new user"""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)
    role: UserRole = Field(default=UserRole.READONLY)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response (no password)"""
    
    user_id: str
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class TokenRequest(BaseModel):
    """Login request"""
    
    username: str = Field(...)
    password: str = Field(...)


class TokenResponse(BaseModel):
    """Login response"""
    
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = Field(default=1800, description="Token expiration in seconds")
