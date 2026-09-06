from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.authorization import (
    INCIDENTS_READ,
    SETTINGS_MANAGE,
    TENANTS_MANAGE,
    USERS_MANAGE,
    is_platform_owner,
    require_permission,
    resolve_tenant_context,
)
from app.db.models import (
    Incident,
    Tenant,
    TenantConfiguration,
    EvidenceChunk,
    ReportJob,
    TenantProvenance,
    TenantStatus,
    User,
)
from app.db.session import get_db
from app.schemas.tenant import (
    CreateTenantRequest,
    TenantConfigurationOut,
    TenantConfigurationUpdate,
    TenantOut,
    TenantUpdateRequest,
    TenantUserCreateRequest,
    TenantUserOut,
    TenantUserUpdateRequest,
)
from app.services.audit_service import record_audit_event
from app.services.tenant_provisioning import TenantProvisioningError, TenantProvisioningService

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _tenant_or_404(db: Session, tenant_id: str, user: User) -> Tenant:
    context = resolve_tenant_context(db, user, tenant_id)
    tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
    if tenant is None:
        raise HTTPException(404, "Tenant not found")
    return tenant


def _tenant_out(db: Session, tenant: Tenant) -> TenantOut:
    return TenantOut(
        **{key: getattr(tenant, key) for key in (
            "id", "name", "description", "tenant_type", "provenance", "status", "industry",
            "website", "contact_email", "contact_phone", "country", "timezone",
            "created_at", "updated_at",
        )},
        user_count=db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar() or 0,
        incident_count=db.query(func.count(Incident.id)).filter(Incident.tenant_id == tenant.id).scalar() or 0,
        evidence_count=db.query(func.count(EvidenceChunk.id)).filter(EvidenceChunk.tenant_id == tenant.id).scalar() or 0,
        report_count=db.query(func.count(ReportJob.id)).filter(ReportJob.tenant_id == tenant.id).scalar() or 0,
        configured=db.query(TenantConfiguration.id).filter(TenantConfiguration.tenant_id == tenant.id).first() is not None,
    )


@router.post("", response_model=TenantOut, status_code=201)
def create_tenant(
    payload: CreateTenantRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(TENANTS_MANAGE)),
):
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform owner required")
    try:
        tenant = TenantProvisioningService(db).create_tenant(payload, user)
    except TenantProvisioningError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _tenant_out(db, tenant)


@router.get("", response_model=list[TenantOut])
def list_tenants(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(TENANTS_MANAGE)),
):
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform permission required")
    legitimate = (
        TenantProvenance.LEGITIMATE_DEMO.value,
        TenantProvenance.LEGITIMATE_CUSTOMER.value,
    )
    tenants = db.query(Tenant).filter(Tenant.provenance.in_(legitimate)).order_by(Tenant.name).all()
    return [_tenant_out(db, tenant) for tenant in tenants]


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(INCIDENTS_READ)),
):
    return _tenant_out(db, _tenant_or_404(db, tenant_id, user))


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: str,
    payload: TenantUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(SETTINGS_MANAGE)),
):
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform owner required")
    tenant = _tenant_or_404(db, tenant_id, user)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        duplicate = (
            db.query(Tenant.id)
            .filter(Tenant.name == changes["name"], Tenant.id != tenant.id)
            .first()
        )
        if duplicate:
            raise HTTPException(409, "A tenant with this name already exists")
    previous_status = tenant.status
    for key, value in changes.items():
        setattr(tenant, key, value)
    action = "tenant.status.changed" if "status" in changes else "tenant.updated"
    record_audit_event(
        db,
        user,
        action,
        "tenant",
        tenant.id,
        tenant_id=tenant.id,
        request=request,
        metadata={"old_status": previous_status, "new_status": tenant.status}
        if "status" in changes
        else None,
    )
    db.commit()
    db.refresh(tenant)
    return _tenant_out(db, tenant)


@router.post("/{tenant_id}/suspend", response_model=TenantOut)
def suspend_tenant(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(TENANTS_MANAGE)),
):
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform owner required")
    tenant = _tenant_or_404(db, tenant_id, user)
    previous_status = tenant.status
    tenant.status = TenantStatus.SUSPENDED.value
    record_audit_event(
        db,
        user,
        "tenant.status.changed",
        "tenant",
        tenant.id,
        tenant_id=tenant.id,
        request=request,
        metadata={"old_status": previous_status, "new_status": tenant.status},
    )
    db.commit()
    db.refresh(tenant)
    return _tenant_out(db, tenant)


@router.post("/{tenant_id}/reactivate", response_model=TenantOut)
def reactivate_tenant(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(TENANTS_MANAGE)),
):
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform owner required")
    tenant = _tenant_or_404(db, tenant_id, user)
    previous_status = tenant.status
    tenant.status = TenantStatus.ACTIVE.value
    record_audit_event(
        db,
        user,
        "tenant.status.changed",
        "tenant",
        tenant.id,
        tenant_id=tenant.id,
        request=request,
        metadata={"old_status": previous_status, "new_status": tenant.status},
    )
    db.commit()
    db.refresh(tenant)
    return _tenant_out(db, tenant)


@router.post("/{tenant_id}/deactivate", response_model=TenantOut)
def deactivate_tenant(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(TENANTS_MANAGE)),
):
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform owner required")
    tenant = _tenant_or_404(db, tenant_id, user)
    previous_status = tenant.status
    tenant.status = TenantStatus.INACTIVE.value
    record_audit_event(
        db,
        user,
        "tenant.status.changed",
        "tenant",
        tenant.id,
        tenant_id=tenant.id,
        request=request,
        metadata={"old_status": previous_status, "new_status": tenant.status},
    )
    db.commit()
    db.refresh(tenant)
    return _tenant_out(db, tenant)


@router.get("/{tenant_id}/configuration", response_model=TenantConfigurationOut)
def get_configuration(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(SETTINGS_MANAGE)),
):
    tenant = _tenant_or_404(db, tenant_id, user)
    config = db.query(TenantConfiguration).filter(TenantConfiguration.tenant_id == tenant.id).first()
    if config is None:
        raise HTTPException(404, "Tenant configuration not found")
    return config


@router.patch("/{tenant_id}/configuration", response_model=TenantConfigurationOut)
def update_configuration(
    tenant_id: str,
    payload: TenantConfigurationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(SETTINGS_MANAGE)),
):
    tenant = _tenant_or_404(db, tenant_id, user)
    config = db.query(TenantConfiguration).filter(TenantConfiguration.tenant_id == tenant.id).first()
    if config is None:
        raise HTTPException(404, "Tenant configuration not found")
    config.configuration = payload.configuration
    record_audit_event(
        db,
        user,
        "tenant.configuration_updated",
        "tenant_configuration",
        config.id,
        tenant_id=tenant.id,
        request=request,
    )
    db.commit()
    db.refresh(config)
    return config


@router.post("/{tenant_id}/workspace")
def enter_workspace(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(INCIDENTS_READ)),
):
    """Validate and audit an explicit tenant workspace selection."""
    tenant = _tenant_or_404(db, tenant_id, user)
    if not is_platform_owner(user) and tenant.id != user.tenant_id:
        raise HTTPException(404, "Tenant not found")
    record_audit_event(
        db,
        user,
        "tenant.workspace_entered",
        "tenant",
        tenant.id,
        tenant_id=tenant.id,
        request=request,
    )
    db.commit()
    return {"tenant_id": tenant.id, "name": tenant.name}


@router.get("/{tenant_id}/users", response_model=list[TenantUserOut])
def list_tenant_users(
    tenant_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(USERS_MANAGE)),
):
    tenant = _tenant_or_404(db, tenant_id, user)
    return db.query(User).filter(User.tenant_id == tenant.id).order_by(User.email).all()


@router.post("/{tenant_id}/users", response_model=TenantUserOut, status_code=201)
def create_tenant_user(
    tenant_id: str,
    payload: TenantUserCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(USERS_MANAGE)),
):
    tenant = _tenant_or_404(db, tenant_id, user)
    try:
        created = TenantProvisioningService(db).create_user(tenant, payload, user)
        db.commit()
    except TenantProvisioningError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    return created


@router.patch("/{tenant_id}/users/{user_id}", response_model=TenantUserOut)
def update_tenant_user(
    tenant_id: str,
    user_id: str,
    payload: TenantUserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(USERS_MANAGE)),
):
    tenant = _tenant_or_404(db, tenant_id, user)
    target = db.query(User).filter(User.id == user_id, User.tenant_id == tenant.id).first()
    if target is None:
        raise HTTPException(404, "User not found")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("role") == "owner":
        raise HTTPException(422, "owner cannot be assigned to a tenant user")
    if target.role == "owner":
        raise HTTPException(403, "Platform owner cannot be modified as a tenant user")
    for key, value in changes.items():
        setattr(target, key, value.value if hasattr(value, "value") else value)
    action = "user.role_changed" if "role" in changes else "user.disabled" if target.status == "DISABLED" else "user.updated"
    record_audit_event(db, user, action, "user", target.id, tenant_id=tenant.id, request=request, metadata={"role": target.role, "status": target.status})
    db.commit()
    db.refresh(target)
    return target
