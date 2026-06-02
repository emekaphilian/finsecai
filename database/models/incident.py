"""
Incident model - Security incidents and alerts
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid
from enum import Enum as PyEnum

from database.core import Base


class IncidentStatus(PyEnum):
    """Incident status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class IncidentSeverity(PyEnum):
    """Incident severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(Base):
    """Incident model for tracking security incidents"""
    
    __tablename__ = "incidents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Incident identifiers
    incident_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Associated transaction
    transaction_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    # Status & severity
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False, index=True)
    severity = Column(Enum(IncidentSeverity), nullable=False, index=True)
    
    # Description & notes
    description = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    
    # Tags for categorization
    tags = Column(ARRAY(String), default=[], nullable=True)
    
    # Assigned analyst
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, default={}, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), default="system", nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Incident(incident_id={self.incident_id}, severity={self.severity}, status={self.status})>"
