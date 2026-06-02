"""
Incident Service - Incident lifecycle management

Manages incident creation, updates, retrieval, and escalation.
With PostgreSQL persistence.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from api.database.repositories import IncidentRepository
from api.database.models import Incident

logger = logging.getLogger(__name__)



class IncidentService:
    """
    Service for managing incident lifecycle
    With database persistence
    """
    
    def __init__(self, db: Session):
        self.logger = logger
        self.db = db
        self.repo = IncidentRepository(db)
    
    def create_incident(
        self,
        transaction_id: str,
        user_id: str,
        severity: str,
        description: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> str:
        """Create a new incident"""
        from datetime import datetime
        import uuid
        
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
        
        incident_data = {
            "id": incident_id,
            "transaction_id": transaction_id,
            "user_id": user_id,
            "severity": severity.lower(),
            "status": "open",
            "description": description,
            "tags": tags or [],
            "metadata": metadata or {}
        }
        
        incident = self.repo.create_with_audit(incident_data, actor=created_by)
        self.logger.info(f"Created incident {incident_id} for user {user_id}")
        
        return incident_id
    
    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident by ID"""
        incident = self.repo.get_by_id(incident_id)
        
        if not incident:
            return None
        
        return self._incident_to_dict(incident)
    
    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List incidents with optional filters"""
        incidents = self.repo.list_with_filters(
            status=status,
            severity=severity,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        return [self._incident_to_dict(inc) for inc in incidents]
    
    def get_high_risk_incidents(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get high-risk incidents"""
        incidents = self.repo.list_high_risk(min_risk_score=0.7, skip=skip, limit=limit)
        return [self._incident_to_dict(inc) for inc in incidents]
    
    def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any],
        updated_by: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Update an incident"""
        incident = self.repo.update_with_audit(incident_id, updates, actor=updated_by)
        
        if not incident:
            return None
        
        return self._incident_to_dict(incident)
    
    def escalate_incident(self, incident_id: str, actor: str = "system") -> Optional[Dict[str, Any]]:
        """Escalate incident to higher severity"""
        incident = self.repo.escalate(incident_id, actor=actor)
        
        if not incident:
            return None
        
        self.logger.info(f"Escalated incident {incident_id} to severity {incident.severity}")
        return self._incident_to_dict(incident)
    
    def resolve_incident(
        self,
        incident_id: str,
        resolution_notes: str,
        actor: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Resolve an incident"""
        incident = self.repo.resolve(incident_id, resolution_notes, actor=actor)
        
        if not incident:
            return None
        
        self.logger.info(f"Resolved incident {incident_id}")
        return self._incident_to_dict(incident)
    
    def get_audit_trail(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for an incident"""
        audit_logs = self.repo.get_audit_trail(incident_id)
        
        return [
            {
                "id": log.id,
                "action": log.action,
                "actor": log.actor,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "details": log.details,
                "created_at": log.created_at.isoformat()
            }
            for log in audit_logs
        ]
    
    def count_incidents_by_status(self, status: str) -> int:
        """Count incidents by status"""
        return self.repo.count_by_status(status)
    
    def count_high_risk_incidents(self) -> int:
        """Count high-risk incidents"""
        return self.repo.count_high_risk(min_risk_score=0.7)
    
    @staticmethod
    def _incident_to_dict(incident: Incident) -> Dict[str, Any]:
        """Convert incident model to dictionary"""
        return {
            "id": incident.id,
            "transaction_id": incident.transaction_id,
            "user_id": incident.user_id,
            "status": incident.status,
            "severity": incident.severity,
            "description": incident.description,
            "tags": incident.tags or [],
            "metadata": incident.metadata or {},
            "risk_score": incident.risk_score,
            "confidence": incident.confidence,
            "evidence_coverage": incident.evidence_coverage,
            "explanation": incident.explanation,
            "governance_flags": incident.governance_flags or [],
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "resolution_notes": incident.resolution_notes
        }

