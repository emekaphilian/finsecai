"""Persist security-relevant actions without storing credentials or tokens."""

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, User

_INHERIT_ACTOR_TENANT = object()


def record_audit_event(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: str,
    *,
    result: str = "success",
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
    tenant_id: str | None | object = _INHERIT_ACTOR_TENANT,
) -> AuditEvent:
    """Stage an audit record; the caller commits with the business action."""
    context = dict(metadata or {})
    if request is not None:
        if request.client:
            context["ip_address"] = request.client.host
        user_agent = request.headers.get("user-agent")
        if user_agent:
            context["user_agent"] = user_agent[:512]
        request_id = request.headers.get("x-request-id")
        if request_id:
            context["request_id"] = request_id[:128]
    event = AuditEvent(
        actor_user_id=user.id,
        tenant_id=user.tenant_id if tenant_id is _INHERIT_ACTOR_TENANT else tenant_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        metadata_json=context or None,
    )
    db.add(event)
    return event
