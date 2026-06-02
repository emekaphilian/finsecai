"""
Risk Score model - Historical risk assessments
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from database.core import Base


class RiskScore(Base):
    """Risk score model for storing risk assessment history"""
    
    __tablename__ = "risk_scores"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transaction reference
    transaction_id = Column(String(100), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    # Risk assessment
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    evidence_coverage = Column(Float, nullable=False)
    
    # AI model info
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    
    # Analysis details
    explanation = Column(String(1000), nullable=True)
    governance_flags = Column(JSON, default=[], nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<RiskScore(transaction_id={self.transaction_id}, risk_level={self.risk_level}, score={self.risk_score})>"
