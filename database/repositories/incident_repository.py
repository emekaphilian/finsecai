"""
Incident repository - Incident database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
import uuid
from datetime import datetime

from database.models import Incident, IncidentStatus, IncidentSeverity


class IncidentRepository:
    """Repository for incident operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_incident(
        self,
        incident_id: str,
        transaction_id: str,
        user_id: str,
        severity: IncidentSeverity,
        description: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None
    ) -> Incident:
        """Create a new incident"""
        incident = Incident(
            incident_id=incident_id,
            transaction_id=transaction_id,
            user_id=user_id,
            severity=severity,
            description=description,
            tags=tags or [],
            metadata=metadata or {},
            status=IncidentStatus.OPEN,
            created_by="system"
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident
    
    def get_incident_by_id(self, incident_id_uuid: uuid.UUID) -> Optional[Incident]:
        """Get incident by UUID"""
        return self.db.query(Incident).filter(Incident.id == incident_id_uuid).first()
    
    def get_incident_by_incident_id(self, incident_id: str) -> Optional[Incident]:
        """Get incident by incident_id string"""
        return self.db.query(Incident).filter(Incident.incident_id == incident_id).first()
    
    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """List incidents with filters - returns (incidents, total_count)"""
        query = self.db.query(Incident)
        
        if status:
            query = query.filter(Incident.status == status)
        if severity:
            query = query.filter(Incident.severity == severity)
        if user_id:
            query = query.filter(Incident.user_id == user_id)
        
        total = query.count()
        incidents = query.order_by(Incident.created_at.desc()).offset(skip).limit(limit).all()
        
        return incidents, total
    
    def update_incident(
        self,
        incident_id_uuid: uuid.UUID,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        description: Optional[str] = None,
        resolution_notes: Optional[str] = None
    ) -> Optional[Incident]:
        """Update incident"""
        incident = self.get_incident_by_id(incident_id_uuid)
        if not incident:
            return None
        
        if status:
            incident.status = status
        if severity:
            incident.severity = severity
        if description:
            incident.description = description
        if resolution_notes:
            incident.resolution_notes = resolution_notes
            incident.resolved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(incident)
        return incident
    
    def escalate_incident(self, incident_id_uuid: uuid.UUID) -> Optional[Incident]:
        """Escalate incident"""
        incident = self.get_incident_by_id(incident_id_uuid)
        if not incident:
            return None
        
        # Update status if not already escalated
        if incident.status != IncidentStatus.ESCALATED:
            incident.status = IncidentStatus.ESCALATED
        
        # Increase severity if possible
        severity_order = [
            IncidentSeverity.LOW,
            IncidentSeverity.MEDIUM,
            IncidentSeverity.HIGH,
            IncidentSeverity.CRITICAL
        ]
        
        current_idx = severity_order.index(incident.severity)
        if current_idx < len(severity_order) - 1:
            incident.severity = severity_order[current_idx + 1]
        
        incident.escalated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(incident)
        return incident
    
    def delete_incident(self, incident_id_uuid: uuid.UUID) -> bool:
        """Delete incident"""
        incident = self.get_incident_by_id(incident_id_uuid)
        if not incident:
            return False
        
        self.db.delete(incident)
        self.db.commit()
        return True
