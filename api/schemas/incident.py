"""
Incident management schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class IncidentStatus(str, Enum):
    """Incident status enumeration"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCreateRequest(BaseModel):
    """Create new incident"""
    
    transaction_id: str = Field(..., description="Associated transaction ID")
    user_id: str = Field(..., description="Affected user ID")
    severity: IncidentSeverity = Field(..., description="Incident severity")
    description: str = Field(..., description="Incident description")
    tags: List[str] = Field(default_factory=list, description="Incident tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class IncidentUpdateRequest(BaseModel):
    """Update existing incident"""
    
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    resolution_notes: Optional[str] = None


class IncidentResponse(BaseModel):
    """Incident response schema"""
    
    incident_id: str = Field(..., description="Unique incident identifier")
    transaction_id: str = Field(..., description="Associated transaction ID")
    user_id: str = Field(..., description="Affected user ID")
    status: IncidentStatus = Field(default=IncidentStatus.OPEN, description="Current status")
    severity: IncidentSeverity = Field(..., description="Severity level")
    description: str = Field(..., description="Description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        example = {
            "incident_id": "INC-2024-001",
            "transaction_id": "TXN-2024-001",
            "user_id": "USER-123",
            "status": "open",
            "severity": "high",
            "description": "Suspicious transaction detected",
            "created_at": "2024-06-02T10:30:00",
            "updated_at": "2024-06-02T10:30:00",
            "tags": ["fraud", "risk"],
            "metadata": {}
        }
