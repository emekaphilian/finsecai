"""
Incident Repository - Specialized data access for incidents
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from api.database.models import Incident, AuditLog
from api.database.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    """Repository for incident data access"""
    
    def __init__(self, session: Session):
        super().__init__(session, Incident)
    
    def get_by_id(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID"""
        return self.session.query(Incident).filter(Incident.id == incident_id).first()
    
    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Incident]:
        """Get all incidents for a user"""
        return self.session.query(Incident).filter(
            Incident.user_id == user_id
        ).order_by(desc(Incident.created_at)).offset(skip).limit(limit).all()
    
    def list_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Incident]:
        """Get incidents by status"""
        return self.session.query(Incident).filter(
            Incident.status == status
        ).order_by(desc(Incident.created_at)).offset(skip).limit(limit).all()
    
    def list_by_severity(self, severity: str, skip: int = 0, limit: int = 100) -> List[Incident]:
        """Get incidents by severity"""
        return self.session.query(Incident).filter(
            Incident.severity == severity
        ).order_by(desc(Incident.risk_score)).offset(skip).limit(limit).all()
    
    def list_high_risk(self, min_risk_score: float = 0.7, skip: int = 0, limit: int = 100) -> List[Incident]:
        """Get high-risk incidents"""
        return self.session.query(Incident).filter(
            Incident.risk_score >= min_risk_score
        ).order_by(desc(Incident.risk_score)).offset(skip).limit(limit).all()
    
    def list_with_filters(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents with multiple filters"""
        query = self.session.query(Incident)
        
        if status:
            query = query.filter(Incident.status == status)
        if severity:
            query = query.filter(Incident.severity == severity)
        if user_id:
            query = query.filter(Incident.user_id == user_id)
        
        return query.order_by(desc(Incident.created_at)).offset(skip).limit(limit).all()
    
    def create_with_audit(self, incident_data: dict, actor: str = "system") -> Incident:
        """Create incident with audit log"""
        incident = self.create(incident_data)
        
        # Log creation
        self.add_audit_log(
            incident_id=incident.id,
            action="created",
            actor=actor,
            new_state=incident_data
        )
        
        return incident
    
    def update_with_audit(self, incident_id: str, updates: dict, actor: str = "system") -> Optional[Incident]:
        """Update incident with audit log"""
        incident = self.get_by_id(incident_id)
        if not incident:
            return None
        
        # Capture previous state
        previous_state = {
            "status": incident.status,
            "severity": incident.severity,
            "description": incident.description
        }
        
        # Update
        incident = self.update(incident_id, updates)
        
        # Log change
        self.add_audit_log(
            incident_id=incident_id,
            action="updated",
            actor=actor,
            previous_state=previous_state,
            new_state=updates
        )
        
        return incident
    
    def escalate(self, incident_id: str, actor: str = "system") -> Optional[Incident]:
        """Escalate incident to higher severity"""
        incident = self.get_by_id(incident_id)
        if not incident:
            return None
        
        severity_order = ["low", "medium", "high", "critical"]
        current_idx = severity_order.index(incident.severity) if incident.severity in severity_order else 0
        
        if current_idx < len(severity_order) - 1:
            new_severity = severity_order[current_idx + 1]
            return self.update_with_audit(
                incident_id,
                {
                    "severity": new_severity,
                    "status": "escalated" if incident.status == "open" else incident.status
                },
                actor=actor
            )
        
        return incident
    
    def resolve(self, incident_id: str, resolution_notes: str, actor: str = "system") -> Optional[Incident]:
        """Mark incident as resolved"""
        incident = self.get_by_id(incident_id)
        if not incident:
            return None
        
        return self.update_with_audit(
            incident_id,
            {
                "status": "resolved",
                "resolution_notes": resolution_notes,
                "resolved_at": datetime.utcnow()
            },
            actor=actor
        )
    
    def add_audit_log(
        self,
        incident_id: str,
        action: str,
        actor: str = "system",
        previous_state: dict = None,
        new_state: dict = None,
        details: str = None
    ) -> AuditLog:
        """Add audit log entry"""
        audit_log = AuditLog(
            incident_id=incident_id,
            action=action,
            actor=actor,
            previous_state=previous_state,
            new_state=new_state,
            details=details
        )
        self.session.add(audit_log)
        self.session.commit()
        return audit_log
    
    def get_audit_trail(self, incident_id: str) -> List[AuditLog]:
        """Get complete audit trail for an incident"""
        return self.session.query(AuditLog).filter(
            AuditLog.incident_id == incident_id
        ).order_by(AuditLog.created_at).all()
    
    def count_by_status(self, status: str) -> int:
        """Count incidents by status"""
        return self.session.query(Incident).filter(Incident.status == status).count()
    
    def count_high_risk(self, min_risk_score: float = 0.7) -> int:
        """Count high-risk incidents"""
        return self.session.query(Incident).filter(Incident.risk_score >= min_risk_score).count()
