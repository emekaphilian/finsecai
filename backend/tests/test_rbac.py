from itertools import product

import pytest
from fastapi import HTTPException

from app.core.authorization import (
    ALL_PERMISSIONS,
    COMPLIANCE_AUDIT_EXPORT,
    COMPLIANCE_READ,
    COMPLIANCE_STR_CREATE,
    COMPLIANCE_STR_SUBMIT,
    COMPLIANCE_STR_UPDATE,
    INCIDENTS_INVESTIGATE,
    INCIDENTS_READ,
    ROLE_PERMISSIONS,
    TenantContext,
    USERS_MANAGE,
    apply_tenant_scope,
    is_platform_owner,
    permissions_for_role,
    resolve_tenant_context,
)


@pytest.mark.parametrize("role,permission", product(ROLE_PERMISSIONS, ALL_PERMISSIONS))
def test_role_permission_matrix(role, permission):
    expected = permission in ROLE_PERMISSIONS[role]
    assert (permission in permissions_for_role(role)) is expected


def _login_as(client, db_session, role, tenant_name, email):
    from app.core.security import hash_password
    from app.db.models import Tenant, User

    tenant = Tenant(name=tenant_name)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        email=email, hashed_password=hash_password("securepass"), tenant_id=tenant.id, role=role
    )
    db_session.add(user)
    db_session.commit()
    response = client.post("/auth/login", data={"username": email, "password": "securepass"})
    return tenant, user, {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_unauthenticated_compliance_request_is_401(client):
    assert client.get("/compliance/str-candidates").status_code == 401


def test_viewer_cannot_create_str_and_analyst_cannot_submit(client, db_session):
    from app.db.models import Incident

    tenant, _, viewer_headers = _login_as(
        client, db_session, "viewer", "Viewer Tenant", "viewer@test"
    )
    incident = Incident(
        tenant_id=tenant.id, user_id="u", amount=1, risk_score=0.9, anomaly_score=0.1
    )
    db_session.add(incident)
    db_session.commit()
    assert (
        client.post(
            "/compliance/str", json={"incident_id": incident.id}, headers=viewer_headers
        ).status_code
        == 403
    )
    _, _, analyst_headers = _login_as(
        client, db_session, "analyst", "Analyst Tenant", "analyst@test"
    )
    assert (
        client.post(
            f"/compliance/str/{incident.id}/submit", json={}, headers=analyst_headers
        ).status_code
        == 403
    )


def test_compliance_officer_workflow_and_audit_events(client, db_session):
    from app.db.models import AuditEvent, Incident

    tenant, _, headers = _login_as(
        client, db_session, "compliance_officer", "Officer Tenant", "officer@test"
    )
    incident = Incident(
        tenant_id=tenant.id, user_id="u", amount=1, risk_score=0.9, anomaly_score=0.1
    )
    db_session.add(incident)
    db_session.commit()
    created = client.post(
        "/compliance/str", json={"incident_id": incident.id, "narrative": "review"}, headers=headers
    )
    assert created.status_code == 201
    str_id = created.json()["id"]
    assert (
        client.patch(
            f"/compliance/str/{str_id}", json={"narrative": "updated"}, headers=headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/compliance/str/{str_id}/submit",
            json={"submission_reference": "NFIU-1"},
            headers=headers,
        ).status_code
        == 200
    )
    actions = {
        event.action
        for event in db_session.query(AuditEvent).filter(AuditEvent.tenant_id == tenant.id)
    }
    assert {"compliance.str.create", "compliance.str.update", "compliance.str.submit"} <= actions


def test_export_permission_and_tenant_isolation(client, db_session):
    from app.db.models import AuditEvent, Incident

    tenant_a, _, admin_headers = _login_as(
        client, db_session, "admin", "Admin Tenant", "admin@test"
    )
    tenant_b, _, viewer_headers = _login_as(
        client, db_session, "viewer", "Other Tenant", "other@test"
    )
    db_session.add_all(
        [
            Incident(
                tenant_id=tenant_a.id, user_id="a", amount=1, risk_score=0.9, anomaly_score=0.1
            ),
            Incident(
                tenant_id=tenant_b.id, user_id="b", amount=2, risk_score=0.9, anomaly_score=0.1
            ),
        ]
    )
    db_session.commit()
    params = {"start_date": "2020-01-01T00:00:00", "end_date": "2030-01-01T00:00:00"}
    assert (
        client.get("/compliance/audit-export", params=params, headers=viewer_headers).status_code
        == 403
    )
    response = client.get("/compliance/audit-export", params=params, headers=admin_headers)
    assert response.status_code == 200
    assert [row["user_id"] for row in response.json()["rows"]] == ["a"]
    assert (
        db_session.query(AuditEvent).filter(AuditEvent.action == "compliance.audit.export").count()
        == 1
    )


def test_cross_tenant_str_is_not_disclosed(client, db_session):
    from app.db.models import Incident

    tenant_a, _, officer_headers = _login_as(
        client, db_session, "compliance_officer", "Tenant A", "a@test"
    )
    tenant_b, _, admin_headers = _login_as(client, db_session, "admin", "Tenant B", "b@test")
    incident = Incident(
        tenant_id=tenant_b.id, user_id="b", amount=1, risk_score=0.9, anomaly_score=0.1
    )
    db_session.add(incident)
    db_session.commit()
    report = client.post(
        "/compliance/str", json={"incident_id": incident.id}, headers=admin_headers
    )
    assert report.status_code == 201
    assert (
        client.patch(
            f"/compliance/str/{report.json()['id']}",
            json={"narrative": "no"},
            headers=officer_headers,
        ).status_code
        == 404
    )


def test_owner_has_platform_scope_and_its_actions_are_audited(client, db_session):
    from app.db.models import AuditEvent, Incident, Tenant, User

    owner_tenant = db_session.query(Tenant).filter(Tenant.name == "Platform Tenant").first()
    if owner_tenant is None:
        owner_tenant = Tenant(
            name="Platform Tenant",
            provenance="LEGITIMATE_DEMO",
        )
        db_session.add(owner_tenant)
        db_session.flush()
    from app.core.security import hash_password

    owner_user = User(
        email="owner@test",
        hashed_password=hash_password("securepass"),
        role="owner",
        tenant_id=owner_tenant.id,
    )
    db_session.add(owner_user)
    db_session.flush()
    owner_headers = {
        "Authorization": "Bearer "
        f"{client.post('/auth/login', data={'username': 'owner@test', 'password': 'securepass'}).json()['access_token']}"
    }

    tenant_b = db_session.query(Tenant).filter(Tenant.name == "Tenant B Owner Test").first()
    if tenant_b is None:
        tenant_b = Tenant(
            name="Tenant B Owner Test",
            provenance="LEGITIMATE_CUSTOMER",
        )
        db_session.add(tenant_b)
        db_session.flush()
    admin_user = User(
        email="admin-owner@test",
        hashed_password="x",
        role="admin",
        tenant_id=tenant_b.id,
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.add_all(
        [
            Incident(
                tenant_id=owner_tenant.id,
                user_id="owner-home",
                amount=1,
                risk_score=0.9,
                anomaly_score=0.1,
            ),
            Incident(
                tenant_id=tenant_b.id,
                user_id="other-tenant",
                amount=2,
                risk_score=0.9,
                anomaly_score=0.1,
            ),
        ]
    )
    db_session.commit()
    incidents = client.get("/incidents", headers=owner_headers)
    assert incidents.status_code == 200
    assert {row["user_id"] for row in incidents.json()} == {"owner-home", "other-tenant"}
    params = {"start_date": "2020-01-01T00:00:00", "end_date": "2030-01-01T00:00:00"}
    export = client.get("/compliance/audit-export", params=params, headers=owner_headers)
    assert export.status_code == 200
    assert {row["user_id"] for row in export.json()["rows"]} == {"owner-home", "other-tenant"}
    event = (
        db_session.query(AuditEvent).filter(AuditEvent.action == "compliance.audit.export").one()
    )
    assert event.metadata_json["scope"] == "platform"


def test_permission_constants_cover_specification():
    assert ALL_PERMISSIONS == {
        INCIDENTS_READ,
        INCIDENTS_INVESTIGATE,
        COMPLIANCE_READ,
        COMPLIANCE_STR_CREATE,
        COMPLIANCE_STR_UPDATE,
        COMPLIANCE_STR_SUBMIT,
        COMPLIANCE_AUDIT_EXPORT,
        USERS_MANAGE,
        "reports:read",
        "reports:generate",
        "reports:export",
        "system:manage",
        "tenants:manage",
        "roles:manage",
        "permissions:manage",
        "settings:manage",
        "audit:read",
        "audit:export",
        "integrations:manage",
        "llm:manage",
        "models:manage",
        "probes:manage",
    }


def test_owner_global_scope_only_includes_legitimate_customer_tenants(db_session):
    from app.db.models import Incident, Tenant, TenantProvenance, User
    from app.core.security import hash_password

    legitimate = Tenant(
        name="Legitimate Tenant",
        provenance=TenantProvenance.LEGITIMATE_CUSTOMER.value,
    )
    benchmark = Tenant(
        name="Benchmark Tenant",
        provenance=TenantProvenance.BENCHMARK.value,
    )
    db_session.add_all([legitimate, benchmark])
    db_session.flush()
    owner = User(
        email="global-owner@test",
        hashed_password=hash_password("securepass"),
        role="owner",
        tenant_id=None,
    )
    db_session.add(owner)
    db_session.add_all(
        [
            Incident(
                tenant_id=legitimate.id,
                user_id="legit-user",
                amount=1,
                risk_score=0.1,
                anomaly_score=0.1,
            ),
            Incident(
                tenant_id=benchmark.id,
                user_id="benchmark-user",
                amount=2,
                risk_score=0.9,
                anomaly_score=0.9,
            ),
        ]
    )
    db_session.commit()

    assert resolve_tenant_context(db_session, owner) == TenantContext.global_scope()
    rows = apply_tenant_scope(db_session.query(Incident), Incident, owner).all()
    assert [row.user_id for row in rows] == ["legit-user"]

    with pytest.raises(HTTPException) as exc:
        resolve_tenant_context(db_session, owner, benchmark.id)
    assert exc.value.status_code == 404


def test_owner_and_non_owner_tenant_contexts_are_explicit(db_session):
    from app.db.models import Tenant, User
    from app.core.security import hash_password

    tenant_a = Tenant(name="Context Tenant A", provenance="LEGITIMATE_DEMO")
    tenant_b = Tenant(name="Context Tenant B", provenance="LEGITIMATE_CUSTOMER")
    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()
    owner = User(
        email="context-owner@test",
        hashed_password=hash_password("securepass"),
        role="owner",
        tenant_id=tenant_a.id,
    )
    analyst = User(
        email="context-analyst@test",
        hashed_password=hash_password("securepass"),
        role="analyst",
        tenant_id=tenant_a.id,
    )
    db_session.add_all([owner, analyst])
    db_session.commit()

    assert resolve_tenant_context(db_session, owner) == TenantContext.global_scope()
    assert resolve_tenant_context(db_session, owner, tenant_b.id) == TenantContext.for_tenant(
        tenant_b.id
    )
    assert resolve_tenant_context(db_session, analyst) == TenantContext.for_tenant(tenant_a.id)

    with pytest.raises(HTTPException) as exc:
        resolve_tenant_context(db_session, analyst, tenant_b.id)
    assert exc.value.status_code == 404


def test_owner_scope_can_be_restricted_to_selected_tenant(db_session):
    from app.db.models import Incident, Tenant, User

    tenant_a = Tenant(name="Scope Tenant A", provenance="LEGITIMATE_DEMO")
    tenant_b = Tenant(name="Scope Tenant B", provenance="LEGITIMATE_CUSTOMER")
    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()
    owner = User(email="scope-owner@test", hashed_password="x", role="owner", tenant_id=tenant_a.id)
    db_session.add(owner)
    db_session.add_all(
        [
            Incident(tenant_id=tenant_a.id, user_id="a", amount=1, risk_score=0.1, anomaly_score=0.1),
            Incident(tenant_id=tenant_b.id, user_id="b", amount=1, risk_score=0.2, anomaly_score=0.2),
        ]
    )
    db_session.commit()

    selected = resolve_tenant_context(db_session, owner, tenant_b.id)
    rows = apply_tenant_scope(db_session.query(Incident), Incident, owner, selected).all()
    assert [row.user_id for row in rows] == ["b"]


def test_owner_report_job_scope_excludes_non_legitimate_tenants(client, db_session):
    from app.core.security import hash_password
    from app.db.models import ReportJob, Tenant, User

    legitimate = Tenant(name="Reports Legitimate", provenance="LEGITIMATE_DEMO")
    benchmark = Tenant(name="Reports Benchmark", provenance="BENCHMARK")
    db_session.add_all([legitimate, benchmark])
    db_session.flush()
    owner = User(
        email="reports-owner@test", hashed_password=hash_password("securepass"), role="owner"
    )
    legitimate_job = ReportJob(tenant_id=legitimate.id, status="completed")
    benchmark_job = ReportJob(tenant_id=benchmark.id, status="completed")
    db_session.add_all([owner, legitimate_job, benchmark_job])
    db_session.commit()
    login = client.post(
        "/auth/login", data={"username": owner.email, "password": "securepass"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.get(f"/reports/jobs/{legitimate_job.id}", headers=headers).status_code == 200
    assert client.get(f"/reports/jobs/{benchmark_job.id}", headers=headers).status_code == 404


def test_owner_audit_scope_excludes_non_legitimate_tenants(client, db_session):
    from app.core.security import hash_password
    from app.db.models import AuditEvent, Tenant, User

    legitimate = Tenant(name="Audit Legitimate", provenance="LEGITIMATE_CUSTOMER")
    diagnostic = Tenant(name="Audit Diagnostic", provenance="DIAGNOSTIC")
    db_session.add_all([legitimate, diagnostic])
    db_session.flush()
    owner = User(email="audit-owner@test", hashed_password=hash_password("securepass"), role="owner")
    db_session.add(owner)
    db_session.flush()
    db_session.add_all(
        [
            AuditEvent(
                actor_user_id=owner.id, tenant_id=legitimate.id, action="legitimate.action",
                resource_type="tenant", resource_id=legitimate.id,
            ),
            AuditEvent(
                actor_user_id=owner.id, tenant_id=diagnostic.id, action="diagnostic.action",
                resource_type="tenant", resource_id=diagnostic.id,
            ),
        ]
    )
    db_session.commit()
    login = client.post(
        "/auth/login", data={"username": owner.email, "password": "securepass"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/audit", headers=headers)
    assert response.status_code == 200
    assert [event["action"] for event in response.json()] == ["legitimate.action"]


def test_admin_is_not_platform_owner():
    from types import SimpleNamespace

    assert is_platform_owner(SimpleNamespace(role="admin")) is False
    assert is_platform_owner(SimpleNamespace(role="owner")) is True
