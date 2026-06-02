"""
Report Service - Report generation and management

Handles report creation, storage, and retrieval.
With PostgreSQL persistence.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from pathlib import Path
import uuid
from sqlalchemy.orm import Session

from api.database.repositories import ReportRepository
from api.database.models import Report

logger = logging.getLogger(__name__)



class ReportService:
    """
    Service for managing incident reports
    With database persistence
    """
    
    def __init__(self, db: Session, reports_dir: str = "./generated_reports"):
        self.logger = logger
        self.db = db
        self.repo = ReportRepository(db)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def create_report(
        self,
        incident_id: str,
        format: str = "pdf",
        title: Optional[str] = None,
        summary: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> str:
        """Create a new report"""
        report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
        
        report_data = {
            "id": report_id,
            "incident_id": incident_id,
            "format": format,
            "title": title or f"Report for Incident {incident_id}",
            "summary": summary or {},
            "content": content,
            "file_path": file_path
        }
        
        if file_path:
            try:
                report_data["file_size"] = Path(file_path).stat().st_size
            except Exception as e:
                self.logger.warning(f"Could not determine file size: {e}")
        
        report = self.repo.create_report(report_data)
        self.logger.info(f"Created report {report_id} for incident {incident_id}")
        
        return report_id
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID"""
        report = self.repo.get_by_id(report_id)
        
        if not report:
            return None
        
        return self._report_to_dict(report)
    
    def list_reports(
        self,
        incident_id: Optional[str] = None,
        format: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List reports"""
        if incident_id:
            reports = self.repo.list_by_incident(incident_id, skip=skip, limit=limit)
        elif format:
            reports = self.repo.list_by_format(format, skip=skip, limit=limit)
        else:
            reports = self.repo.get_all(skip=skip, limit=limit)
        
        return [self._report_to_dict(rep) for rep in reports]
    
    def update_report(
        self,
        report_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a report"""
        report = self.repo.update_report(report_id, updates)
        
        if not report:
            return None
        
        return self._report_to_dict(report)
    
    def delete_report(self, report_id: str) -> bool:
        """Delete a report"""
        report = self.repo.get_by_id(report_id)
        if not report:
            return False
        
        # Delete file if it exists
        if report.file_path:
            try:
                Path(report.file_path).unlink(missing_ok=True)
                self.logger.info(f"Deleted report file: {report.file_path}")
            except Exception as e:
                self.logger.warning(f"Could not delete report file: {e}")
        
        # Delete from database
        success = self.repo.delete_report(report_id)
        
        if success:
            self.logger.info(f"Deleted report {report_id}")
        
        return success
    
    def count_reports_for_incident(self, incident_id: str) -> int:
        """Count reports for an incident"""
        return self.repo.count_by_incident(incident_id)
    
    @staticmethod
    def _report_to_dict(report: Report) -> Dict[str, Any]:
        """Convert report model to dictionary"""
        return {
            "id": report.id,
            "incident_id": report.incident_id,
            "format": report.format,
            "title": report.title,
            "summary": report.summary or {},
            "content": report.content,
            "file_path": report.file_path,
            "file_size": report.file_size,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None
        }
