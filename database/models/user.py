"""
User model - User accounts and authentication
"""

from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum as PyEnum

from database.core import Base


class UserRole(PyEnum):
    """User role enumeration"""
    ADMIN = "admin"
    ANALYST_TIER1 = "analyst_tier1"
    ANALYST_TIER2 = "analyst_tier2"
    READONLY = "readonly"
    API_SERVICE = "api_service"


class User(Base):
    """User account model"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Credentials
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.READONLY, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
