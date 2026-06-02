"""
SQLAlchemy Models for FinSecAI Database
Defines all database tables and relationships
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from api.database import Base


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200))
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="readonly", index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    incidents_created = relationship("Incident", back_populates="created_by_user", foreign_keys="Incident.created_by")
    incidents_updated = relationship("Incident", back_populates="updated_by_user", foreign_keys="Incident.updated_by")
    
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_role_active', 'role', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Transaction(Base):
    """Transaction record model"""
    __tablename__ = "transactions"
    
    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    amount = Column(Float, nullable=False, index=True)
    currency = Column(String(3), default="USD")
    country = Column(String(2), index=True)
    merchant = Column(String(200))
    merchant_category = Column(String(10))
    
    device_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default={})
    
    # Relationships
    incidents = relationship("Incident", back_populates="transaction")
    risk_scores = relationship("RiskScore", back_populates="transaction")
    
    __table_args__ = (
        Index('idx_transaction_user_date', 'user_id', 'created_at'),
        Index('idx_transaction_amount_country', 'amount', 'country'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount})>"


class Incident(Base):
    """Security incident model"""
    __tablename__ = "incidents"
    
    id = Column(String(100), primary_key=True, index=True)
    transaction_id = Column(String(100), ForeignKey("transactions.id"), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    
    status = Column(String(50), default="open", index=True)
    severity = Column(String(50), default="medium", index=True)
    
    description = Column(Text)
    tags = Column(JSON, default=[])
    metadata = Column(JSON, default={})
    
    # AI Analysis
    risk_score = Column(Float, nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    evidence_coverage = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    governance_flags = Column(JSON, default=[])
    
    # Audit Trail
    created_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    updated_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="incidents")
    created_by_user = relationship("User", back_populates="incidents_created", foreign_keys=[created_by])
    updated_by_user = relationship("User", back_populates="incidents_updated", foreign_keys=[updated_by])
    reports = relationship("Report", back_populates="incident", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="incident", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_incident_status_severity', 'status', 'severity'),
        Index('idx_incident_user_date', 'user_id', 'created_at'),
        Index('idx_incident_risk_score', 'risk_score'),
    )
    
    def __repr__(self):
        return f"<Incident(id={self.id}, status={self.status}, severity={self.severity})>"


class RiskScore(Base):
    """Historical risk score tracking"""
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(100), ForeignKey("transactions.id"), index=True, nullable=False)
    
    score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    model_version = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="risk_scores")
    
    __table_args__ = (
        Index('idx_risk_score_transaction_date', 'transaction_id', 'created_at'),
        Index('idx_risk_score_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<RiskScore(transaction_id={self.transaction_id}, score={self.score})>"


class Report(Base):
    """Generated report model"""
    __tablename__ = "reports"
    
    id = Column(String(100), primary_key=True, index=True)
    incident_id = Column(String(100), ForeignKey("incidents.id"), index=True, nullable=False)
    
    format = Column(String(20), default="pdf")  # pdf, json, html
    title = Column(String(500))
    
    summary = Column(JSON, default={})
    content = Column(Text, nullable=True)
    
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="reports")
    
    __table_args__ = (
        Index('idx_report_incident_date', 'incident_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Report(id={self.id}, incident_id={self.incident_id})>"


class AuditLog(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(100), ForeignKey("incidents.id"), index=True, nullable=False)
    
    action = Column(String(100), index=True, nullable=False)
    actor = Column(String(100), nullable=True)  # User ID or system
    
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    
    details = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_log_incident_date', 'incident_id', 'created_at'),
        Index('idx_audit_log_action_date', 'action', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, incident_id={self.incident_id}, action={self.action})>"
