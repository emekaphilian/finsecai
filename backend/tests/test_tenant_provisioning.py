import pytest

from app.core.security import hash_password
from app.db.models import AuditEvent, Incident, Tenant, TenantConfiguration, User
from app.schemas.tenant import CreateTenantRequest
from app.services.tenant_provisioning import TenantProvisioningService


def make_user(db_session, email, role, tenant_id=None):
    user = User(
        email=email,
        hashed_password=hash_password("securepass"),
        role=role,
        tenant_id=tenant_id,
    )
    db_session.add(user)
    db_session.commit()
    return user


def tenant_payload(email="admin@customer.test", role="admin"):
    return {
        "company_name": "Customer One",
        "description": "Customer tenant",
        "industry": "Financial services",
        "timezone": "Africa/Lagos",
        "configuration": {"display_name": "Customer One SOC"},
        "initial_administrator": {"email": email, "password": "securepass", "role": role},
    }


def test_owner_provisioning_creates_customer_configuration_user_and_audit(db_session):
    owner = make_user(db_session, "owner@test", "owner")
    tenant = Tenant(name="Acme Corp", tenant_type="DEMO", status="ACTIVE")
    db_session.add(tenant)
    db_session.commit()

    created = TenantProvisioningService(db_session).create_tenant(
        CreateTenantRequest(**tenant_payload()), owner
    )

    assert created.tenant_type == "CUSTOMER"
    assert created.provenance == "LEGITIMATE_CUSTOMER"
    assert created.status == "ACTIVE"
    assert db_session.query(TenantConfiguration).filter_by(tenant_id=created.id).count() == 1
    initial = db_session.query(User).filter_by(tenant_id=created.id).one()
    assert initial.role == "admin"
    assert db_session.query(Incident).filter_by(tenant_id=created.id).count() == 0
    actions = {
        event.action
        for event in db_session.query(AuditEvent).filter(AuditEvent.tenant_id == created.id)
    }
    assert {"tenant.created", "user.created"} <= actions


def test_tenant_provisioning_rejects_owner_role(db_session):
    owner = make_user(db_session, "owner-role@test", "owner")
    with pytest.raises(ValueError):
        CreateTenantRequest(**tenant_payload("blocked@test", "owner"))
    assert db_session.query(Tenant).filter(Tenant.name == "Customer One").count() == 0
    assert owner.role == "owner"


def test_tenant_provisioning_rolls_back_when_audit_fails(db_session, monkeypatch):
    owner = make_user(db_session, "owner-rollback@test", "owner")
    from app.services import tenant_provisioning
    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(tenant_provisioning, "record_audit_event", fail_audit)
    with pytest.raises(RuntimeError):
        TenantProvisioningService(db_session).create_tenant(
            CreateTenantRequest(**tenant_payload("rollback@test")), owner
        )

    assert db_session.query(Tenant).filter(Tenant.name == "Customer One").count() == 0
    assert db_session.query(User).filter(User.email == "rollback@test").count() == 0


def test_disabled_user_cannot_login(client, db_session):
    tenant = Tenant(name="Disabled User Tenant")
    db_session.add(tenant)
    db_session.flush()
    user = User(
        email="disabled@test",
        hashed_password=hash_password("securepass"),
        role="analyst",
        tenant_id=tenant.id,
        status="DISABLED",
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login", data={"username": "disabled@test", "password": "securepass"}
    )
    assert response.status_code == 401


def test_suspended_tenant_user_cannot_login(client, db_session):
    tenant = Tenant(name="Suspended Tenant", status="SUSPENDED")
    db_session.add(tenant)
    db_session.flush()
    db_session.add(
        User(
            email="suspended@test",
            hashed_password=hash_password("securepass"),
            role="analyst",
            tenant_id=tenant.id,
        )
    )
    db_session.commit()

    response = client.post(
        "/auth/login", data={"username": "suspended@test", "password": "securepass"}
    )
    assert response.status_code == 401
