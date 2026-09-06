"""Centralized, explicit role-to-permission authorization for FinSecAI."""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Tenant, TenantProvenance, User

INCIDENTS_READ = "incidents:read"
INCIDENTS_INVESTIGATE = "incidents:investigate"
COMPLIANCE_READ = "compliance:read"
COMPLIANCE_STR_CREATE = "compliance:str:create"
COMPLIANCE_STR_UPDATE = "compliance:str:update"
COMPLIANCE_STR_SUBMIT = "compliance:str:submit"
COMPLIANCE_AUDIT_EXPORT = "compliance:audit:export"
USERS_MANAGE = "users:manage"
SYSTEM_MANAGE = "system:manage"
TENANTS_MANAGE = "tenants:manage"
ROLES_MANAGE = "roles:manage"
PERMISSIONS_MANAGE = "permissions:manage"
SETTINGS_MANAGE = "settings:manage"
REPORTS_READ = "reports:read"
REPORTS_GENERATE = "reports:generate"
REPORTS_EXPORT = "reports:export"
AUDIT_READ = "audit:read"
AUDIT_EXPORT = "audit:export"
INTEGRATIONS_MANAGE = "integrations:manage"
LLM_MANAGE = "llm:manage"
MODELS_MANAGE = "models:manage"
PROBES_MANAGE = "probes:manage"

TENANT_PERMISSIONS = frozenset(
    {
        INCIDENTS_READ,
        INCIDENTS_INVESTIGATE,
        COMPLIANCE_READ,
        COMPLIANCE_STR_CREATE,
        COMPLIANCE_STR_UPDATE,
        COMPLIANCE_STR_SUBMIT,
        COMPLIANCE_AUDIT_EXPORT,
        USERS_MANAGE,
        REPORTS_READ,
        REPORTS_GENERATE,
        REPORTS_EXPORT,
    }
)

PLATFORM_PERMISSIONS = frozenset(
    {
        SYSTEM_MANAGE,
        TENANTS_MANAGE,
        ROLES_MANAGE,
        PERMISSIONS_MANAGE,
        SETTINGS_MANAGE,
        AUDIT_READ,
        AUDIT_EXPORT,
        INTEGRATIONS_MANAGE,
        LLM_MANAGE,
        MODELS_MANAGE,
        PROBES_MANAGE,
    }
)
ALL_PERMISSIONS = TENANT_PERMISSIONS | PLATFORM_PERMISSIONS
OWNER_ONLY_PERMISSIONS = PLATFORM_PERMISSIONS
KNOWN_PERMISSIONS = ALL_PERMISSIONS

LEGITIMATE_TENANT_PROVENANCE_VALUES = frozenset(
    {
        TenantProvenance.LEGITIMATE_DEMO.value,
        TenantProvenance.LEGITIMATE_CUSTOMER.value,
    }
)

# The Tier 4 permission matrix is the single source of truth. Route handlers
# name a permission, never a role, through require_permission().
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "owner": TENANT_PERMISSIONS | PLATFORM_PERMISSIONS,
    "admin": TENANT_PERMISSIONS,
    "compliance_officer": frozenset(
        {
            INCIDENTS_READ,
            INCIDENTS_INVESTIGATE,
            COMPLIANCE_READ,
            COMPLIANCE_STR_CREATE,
            COMPLIANCE_STR_UPDATE,
            COMPLIANCE_STR_SUBMIT,
            COMPLIANCE_AUDIT_EXPORT,
        }
    ),
    "analyst": frozenset(
        {
            INCIDENTS_READ,
            INCIDENTS_INVESTIGATE,
            COMPLIANCE_READ,
            REPORTS_READ,
            REPORTS_GENERATE,
        }
    ),
    "viewer": frozenset({INCIDENTS_READ, COMPLIANCE_READ, REPORTS_READ}),
}


@dataclass(frozen=True)
class TenantContext:
    """Validated request scope for tenant-owned operations."""

    tenant_id: str | None = None
    is_global: bool = False

    @classmethod
    def global_scope(cls) -> "TenantContext":
        return cls(is_global=True)

    @classmethod
    def for_tenant(cls, tenant_id: str) -> "TenantContext":
        return cls(tenant_id=tenant_id)


def permissions_for_role(role: str | None) -> frozenset[str]:
    """Return no permissions for unrecognized roles (safe default)."""
    return ROLE_PERMISSIONS.get((role or "").strip().lower(), frozenset())


def is_platform_owner(user: User) -> bool:
    """Owner is the only application role that may operate across tenants."""
    return (user.role or "").strip().lower() == "owner"


def _legitimate_tenant_ids_query(db: Session):
    return db.query(Tenant.id).filter(Tenant.provenance.in_(LEGITIMATE_TENANT_PROVENANCE_VALUES))


def apply_enterprise_scope(query, model):
    """Limit a tenant-owned query to the authorized enterprise data boundary.

    This helper deliberately has no user argument: callers must still protect
    the route with an owner-only platform permission.  Keeping the data-boundary
    predicate here prevents privileged endpoints from silently becoming an
    unfiltered query as new tenant provenance classes are introduced.
    """
    return query.filter(model.tenant_id.in_(_legitimate_tenant_ids_query(query.session)))


def resolve_tenant_context(
    db: Session, user: User, requested_tenant_id: str | None = None
) -> TenantContext:
    """Resolve requested scope without trusting caller-supplied tenant IDs."""
    if is_platform_owner(user):
        if requested_tenant_id is None:
            return TenantContext.global_scope()
        tenant = (
            db.query(Tenant)
            .filter(
                Tenant.id == requested_tenant_id,
                Tenant.provenance.in_(LEGITIMATE_TENANT_PROVENANCE_VALUES),
            )
            .first()
        )
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return TenantContext.for_tenant(requested_tenant_id)

    if requested_tenant_id is not None and requested_tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context required")
    return TenantContext.for_tenant(user.tenant_id)


def apply_tenant_scope(query, model, user: User, context: TenantContext | None = None):
    """Apply validated tenant scope; global scope is owner-only over legitimate tenancy data."""
    context = context or resolve_tenant_context(query.session, user)
    if context.is_global:
        if not is_platform_owner(user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return apply_enterprise_scope(query, model)
    return query.filter(model.tenant_id == context.tenant_id)


def require_permission(permission: str) -> Callable:
    if permission not in KNOWN_PERMISSIONS:
        raise ValueError(f"Unknown permission: {permission}")

    def dependency(user: User = Depends(get_current_user)) -> User:
        if permission not in permissions_for_role(user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission for this action",
            )
        return user

    return dependency
