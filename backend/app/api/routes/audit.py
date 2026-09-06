"""Owner-visible enterprise audit trail, constrained to legitimate tenancy."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authorization import AUDIT_READ, apply_enterprise_scope, require_permission
from app.db.models import AuditEvent, User
from app.db.session import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_events(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(AUDIT_READ)),
):
    """Return attributed audit records in the authorized enterprise boundary."""
    events = (
        apply_enterprise_scope(db.query(AuditEvent), AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": event.id,
            "actor_user_id": event.actor_user_id,
            "tenant_id": event.tenant_id,
            "action": event.action,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "result": event.result,
            "metadata": event.metadata_json,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]
