"""
Report Repository - Specialized data access for reports
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from api.database.models import Report
from api.database.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for report data access"""
    
    def __init__(self, session: Session):
        super().__init__(session, Report)
    
    def get_by_id(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        return self.session.query(Report).filter(Report.id == report_id).first()
    
    def list_by_incident(self, incident_id: str, skip: int = 0, limit: int = 100) -> List[Report]:
        """Get all reports for an incident"""
        return self.session.query(Report).filter(
            Report.incident_id == incident_id
        ).order_by(desc(Report.created_at)).offset(skip).limit(limit).all()
    
    def list_by_format(self, format: str, skip: int = 0, limit: int = 100) -> List[Report]:
        """Get reports by format"""
        return self.session.query(Report).filter(
            Report.format == format
        ).order_by(desc(Report.created_at)).offset(skip).limit(limit).all()
    
    def create_report(self, report_data: dict) -> Report:
        """Create new report"""
        return self.create(report_data)
    
    def update_report(self, report_id: str, updates: dict) -> Optional[Report]:
        """Update report"""
        return self.update(report_id, updates)
    
    def delete_report(self, report_id: str) -> bool:
        """Delete report"""
        return self.delete(report_id)
    
    def count_by_incident(self, incident_id: str) -> int:
        """Count reports for an incident"""
        return self.session.query(Report).filter(Report.incident_id == incident_id).count()
