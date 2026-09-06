from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import (
    Tenant,
    TenantConfiguration,
    TenantProvenance,
    TenantStatus,
    TenantType,
    User,
    UserStatus,
)
from app.schemas.tenant import CreateTenantRequest, TenantUserCreateRequest
from app.services.audit_service import record_audit_event

TENANT_ROLES = frozenset({"admin", "compliance_officer", "analyst", "viewer"})
DEFAULT_CONFIGURATION = {
    "display_name": "",
    "default_severity": "medium",
    "enabled_frameworks": ["mitre", "nist"],
    "report": {"format": "pdf"},
    "notifications": {"enabled": False},
    "feature_flags": {},
}


class TenantProvisioningError(ValueError):
    pass


class TenantProvisioningService:
    def __init__(self, db: Session):
        self.db = db

    def create_tenant(self, request: CreateTenantRequest, actor: User) -> Tenant:
        if self.db.query(Tenant.id).filter(Tenant.name == request.company_name).first():
            raise TenantProvisioningError("A tenant with this name already exists")
        if request.initial_administrator.role not in TENANT_ROLES:
            raise TenantProvisioningError("Invalid initial tenant administrator role")
        if self.db.query(User.id).filter(User.email == request.initial_administrator.email).first():
            raise TenantProvisioningError("A user with this email already exists")

        configuration = dict(DEFAULT_CONFIGURATION)
        configuration.update(request.configuration)
        try:
            tenant = Tenant(
                    name=request.company_name,
                    description=request.description,
                    tenant_type=TenantType.CUSTOMER.value,
                    provenance=TenantProvenance.LEGITIMATE_CUSTOMER.value,
                    status=TenantStatus.ACTIVE.value,
                    industry=request.industry,
                    website=request.website,
                    contact_email=request.contact_email,
                    contact_phone=request.contact_phone,
                    country=request.country,
                    timezone=request.timezone,
            )
            self.db.add(tenant)
            self.db.flush()
            self.db.add(
                TenantConfiguration(
                    tenant_id=tenant.id,
                    configuration=configuration,
                )
            )
            initial_user = User(
                    email=request.initial_administrator.email,
                    hashed_password=hash_password(request.initial_administrator.password),
                    role=request.initial_administrator.role,
                    tenant_id=tenant.id,
                    status=UserStatus.ACTIVE.value,
                    must_change_password=True,
            )
            self.db.add(initial_user)
            self.db.flush()
            record_audit_event(
                    self.db,
                    actor,
                    "tenant.created",
                    "tenant",
                    tenant.id,
                    tenant_id=tenant.id,
                    metadata={"tenant_name": tenant.name, "tenant_type": tenant.tenant_type},
            )
            record_audit_event(
                    self.db,
                    actor,
                    "user.created",
                    "user",
                    initial_user.id,
                    tenant_id=tenant.id,
                    metadata={"email": initial_user.email, "role": initial_user.role},
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise TenantProvisioningError("Tenant or user conflicts with existing data") from exc
        except Exception:
            self.db.rollback()
            raise
        return tenant

    def create_user(self, tenant: Tenant, request: TenantUserCreateRequest, actor: User) -> User:
        if request.role not in TENANT_ROLES:
            raise TenantProvisioningError("Invalid tenant user role")
        if self.db.query(User.id).filter(User.email == request.email).first():
            raise TenantProvisioningError("A user with this email already exists")
        user = User(
            email=request.email,
            hashed_password=hash_password(request.password),
            role=request.role,
            tenant_id=tenant.id,
            status=UserStatus.ACTIVE.value,
            must_change_password=True,
        )
        self.db.add(user)
        self.db.flush()
        record_audit_event(
            self.db,
            actor,
            "user.created",
            "user",
            user.id,
            tenant_id=tenant.id,
            metadata={"email": user.email, "role": user.role},
        )
        return user
