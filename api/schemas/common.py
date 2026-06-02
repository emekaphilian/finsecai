"""
Standard HTTP response schemas
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, List
from datetime import datetime


class ErrorDetail(BaseModel):
    """Error detail information"""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional details")


class ErrorResponse(BaseModel):
    """Standard error response"""
    
    status: str = Field(default="error")
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response wrapper"""
    
    status: str = Field(default="success")
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ListResponse(BaseModel):
    """Paginated list response"""
    
    status: str = Field(default="success")
    data: List[Any]
    pagination: Dict[str, int] = Field(
        default_factory=lambda: {"page": 1, "page_size": 20, "total": 0}
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(default="ok")
    service: str = Field(default="FinSecAI API")
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str
