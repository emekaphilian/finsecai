"""
Transaction model - Financial transactions for analysis
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum as PyEnum

from database.core import Base


class TransactionStatus(PyEnum):
    """Transaction status"""
    PENDING = "pending"
    ANALYZED = "analyzed"
    FLAGGED = "flagged"
    RESOLVED = "resolved"


class Transaction(Base):
    """Transaction model for storing transaction records"""
    
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transaction identifiers
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    # Transaction details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    country = Column(String(100), nullable=False)
    
    # Merchant info
    merchant = Column(String(255), nullable=True)
    merchant_category = Column(String(10), nullable=True)
    
    # Device/Network info
    device_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Analysis status
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    
    # Risk assessment
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)
    
    # Associated incident (if created)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, default={}, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    analyzed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount}, risk_level={self.risk_level})>"
