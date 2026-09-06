from app.core.security import hash_password
from app.db.models import Incident, ReportJob, Tenant, User


def add_user(db_session, email, role, tenant_id=None):
    user = User(
        email=email,
        hashed_password=hash_password("securepass"),
        role=role,
        tenant_id=tenant_id,
    )
    db_session.add(user)
    db_session.commit()
    return user


def login(client, email):
    response = client.post(
        "/auth/login", data={"username": email, "password": "securepass"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_owner_enterprise_summary_excludes_historical_non_customers(client, db_session):
    owner_tenant = Tenant(name="Owner Home")
    demo = Tenant(
        name="Acme Corp",
        tenant_type="DEMO",
        provenance="LEGITIMATE_DEMO",
    )
    customer = Tenant(
        name="Legitimate Customer",
        tenant_type="CUSTOMER",
        provenance="LEGITIMATE_CUSTOMER",
        status="ACTIVE",
    )
    benchmark = Tenant(
        name="Benchmark Historical",
        tenant_type=None,
        provenance="BENCHMARK",
    )
    diagnostic = Tenant(
        name="Diagnostic Historical",
        tenant_type=None,
        provenance="DIAGNOSTIC",
    )
    db_session.add_all([owner_tenant, demo, customer, benchmark, diagnostic])
    db_session.flush()
    owner = add_user(db_session, "enterprise-owner@test", "owner", owner_tenant.id)
    db_session.add_all(
        [
            Incident(tenant_id=demo.id, user_id="demo", amount=1, risk_score=0.8, anomaly_score=0.1),
            Incident(tenant_id=customer.id, user_id="customer", amount=2, risk_score=0.4, anomaly_score=0.1),
            Incident(tenant_id=benchmark.id, user_id="benchmark", amount=3, risk_score=0.9, anomaly_score=0.1),
            ReportJob(tenant_id=customer.id, status="completed"),
            ReportJob(tenant_id=customer.id, status="queued"),
            ReportJob(tenant_id=benchmark.id, status="completed"),
        ]
    )
    db_session.commit()

    response = client.get("/analytics/enterprise-summary", headers=login(client, owner.email))

    assert response.status_code == 200
    assert response.json() == {
        "total_tenants": 2,
        "active_customer_tenants": 1,
        "demo_tenants": 1,
        "total_incidents": 2,
        "high_risk_incidents": 1,
        "reports_generated": 1,
    }


def test_tenant_user_cannot_read_enterprise_summary(client, db_session):
    tenant = Tenant(name="Tenant User Home")
    db_session.add(tenant)
    db_session.flush()
    user = add_user(db_session, "tenant-user@test", "analyst", tenant.id)

    response = client.get("/analytics/enterprise-summary", headers=login(client, user.email))

    assert response.status_code == 403
