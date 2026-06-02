"""
Audit Log repository - Audit trail operations
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from database.models import AuditLog, AuditAction


class AuditLogRepository:
    """Repository for audit log operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_audit_log(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            username=username,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_values,
            new_values=new_values,
            status=status or "success",
            error_message=error_message
        )
        self.db.add(log)
        self.db.commit()
        return log
    
    def list_audit_logs(
        self,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple:
        """List audit logs with filters - returns (logs, total_count)"""
        query = self.db.query(AuditLog)
        
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        
        return logs, total
