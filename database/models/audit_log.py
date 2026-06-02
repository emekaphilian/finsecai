"""
Audit Log model - Complete audit trail for compliance
"""

from sqlalchemy import Column, String, DateTime, JSON, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum as PyEnum

from database.core import Base


class AuditAction(PyEnum):
    """Audit log actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    AUTHORIZE = "authorize"
    ESCALATE = "escalate"
    RESOLVE = "resolve"
    EXPORT = "export"


class AuditLog(Base):
    """Audit log model for compliance and forensics"""
    
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    
    # User information
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(50), nullable=True)
    
    # Request details
    request_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp (indexed for forensics)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, resource_type={self.resource_type}, user={self.username})>"
