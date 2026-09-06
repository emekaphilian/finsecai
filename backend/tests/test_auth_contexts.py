from app.core.security import hash_password, verify_password
from app.db.models import Tenant, TenantType, User
from app.seed import ensure_owner_seeded


def test_owner_bootstrap_is_idempotent_and_does_not_reset_password(db_session, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "owner_email", "owner@finsecai.com")
    monkeypatch.setattr(config.settings, "owner_password", "123")
    ensure_owner_seeded(db_session)
    owner = db_session.query(User).filter_by(email="owner@finsecai.com").one()
    owner.hashed_password = hash_password("changed-password")
    db_session.commit()

    ensure_owner_seeded(db_session)
    assert db_session.query(User).filter_by(role="owner").count() == 1
    assert verify_password("changed-password", owner.hashed_password)
    assert not verify_password("123", owner.hashed_password)


def test_default_owner_can_enter_console_without_forced_credential_change(db_session, client, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "owner_email", "owner@finsecai.com")
    monkeypatch.setattr(config.settings, "owner_password", "123")
    ensure_owner_seeded(db_session)

    owner = db_session.query(User).filter_by(email="owner@finsecai.com").one()
    assert verify_password("123", owner.hashed_password)
    assert owner.role == "owner"
    assert owner.tenant_id is None
    assert owner.must_change_password is False

    response = client.post(
        "/auth/owner/login",
        data={"username": "owner@finsecai.com", "password": "123"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "owner"
    assert response.json()["must_change_password"] is False


def test_tenant_provisioned_users_are_temporary(db_session):
    tenant = Tenant(name="Temporary Tenant", tenant_type=TenantType.CUSTOMER.value)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        email="temporary@example.com",
        hashed_password=hash_password("temporary-password"),
        tenant_id=tenant.id,
        role="analyst",
        must_change_password=True,
    )
    db_session.add(user)
    db_session.commit()
    assert db_session.query(User).filter_by(email=user.email).one().must_change_password is True


def test_owner_and_tenant_roles_are_distinct(db_session):
    owner = User(email="owner@example.com", hashed_password=hash_password("securepass"), role="owner")
    tenant = Tenant(name="Isolated Tenant", tenant_type=TenantType.CUSTOMER.value)
    db_session.add_all([owner, tenant])
    db_session.flush()
    tenant_user = User(
        email="user@example.com",
        hashed_password=hash_password("securepass"),
        role="analyst",
        tenant_id=tenant.id,
    )
    db_session.add(tenant_user)
    db_session.commit()
    assert owner.tenant_id is None
    assert tenant_user.tenant_id == tenant.id
    assert tenant_user.role != owner.role
