"""
Report model - Generated security reports
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from database.core import Base


class Report(Base):
    """Report model for tracking generated reports"""
    
    __tablename__ = "reports"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Report identifiers
    report_id = Column(String(100), unique=True, nullable=False, index=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True)
    
    # Report details
    format = Column(String(20), default="pdf", nullable=False)
    title = Column(String(255), nullable=False)
    
    # Generated content (for JSON format, store here)
    content = Column(Text, nullable=True)
    
    # Report location (for file-based reports)
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    
    # Report summary
    summary = Column(JSON, nullable=True)
    
    # Generation info
    generated_by = Column(String(100), default="system", nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<Report(report_id={self.report_id}, incident_id={self.incident_id}, format={self.format})>"
