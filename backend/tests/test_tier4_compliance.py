from datetime import datetime, timedelta, timezone

import pytest


def _authenticated_user(client, db_session, role="analyst", suffix=""):
    from app.core.security import hash_password
    from app.db.models import Tenant, User

    tenant = Tenant(name=f"Tier 4 Compliance Tenant {suffix}")
    db_session.add(tenant)
    db_session.flush()
    email = f"tier4{suffix}@example.com"
    db_session.add(
        User(
            email=email, hashed_password=hash_password("securepass"), tenant_id=tenant.id, role=role
        )
    )
    db_session.commit()
    response = client.post("/auth/login", data={"username": email, "password": "securepass"})
    return tenant, {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_audit_export_json_and_csv_include_model_and_str_data(client, db_session):
    from app.db.models import Incident, MLPredictionAudit

    tenant, headers = _authenticated_user(client, db_session, "compliance_officer", "export")
    incident = Incident(
        tenant_id=tenant.id,
        user_id="u-1",
        amount=5000,
        risk_score=0.92,
        anomaly_score=0.8,
        governance_flags="HIGH_RISK_REVIEW_REQUIRED",
    )
    db_session.add(incident)
    db_session.flush()
    db_session.add(
        MLPredictionAudit(
            tenant_id=tenant.id,
            incident_id=incident.id,
            model_version="v-test",
            risk_score=0.92,
            anomaly_score=0.8,
            confidence=0.9,
            feature_values={},
            feature_contributions=[{"feature": "amount", "value": 5000, "shap": 0.4}],
        )
    )
    db_session.commit()
    start = (datetime.now() - timedelta(days=1)).isoformat()
    end = (datetime.now() + timedelta(days=1)).isoformat()
    response = client.get(
        "/compliance/audit-export", params={"start_date": start, "end_date": end}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["rows"][0]["model_version"] == "v-test"
    assert "amount=5e+03" in response.json()["rows"][0]["top_model_factors"]
    response = client.get(
        "/compliance/audit-export",
        params={"start_date": start, "end_date": end, "format": "csv"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "model_version" in response.text


def test_str_candidate_sla_and_filing_workflow(client, db_session):
    from app.db.models import Incident

    tenant, headers = _authenticated_user(client, db_session, "compliance_officer", "str")
    old = Incident(
        tenant_id=tenant.id,
        user_id="old",
        amount=10,
        risk_score=0.9,
        anomaly_score=0.2,
        created_at=datetime.now() - timedelta(hours=30),
    )
    recent = Incident(
        tenant_id=tenant.id,
        user_id="recent",
        amount=20,
        risk_score=0.9,
        anomaly_score=0.2,
        created_at=datetime.now() - timedelta(hours=2),
    )
    db_session.add_all([old, recent])
    db_session.commit()
    response = client.get("/compliance/str-candidates", headers=headers)
    assert response.status_code == 200
    statuses = {row["incident_id"]: row["sla_status"] for row in response.json()}
    assert statuses[old.id] == "sla_breached"
    assert statuses[recent.id] == "within_sla"
    response = client.post(
        f"/compliance/{recent.id}/mark-str-filed",
        json={"str_reference": "NFIU-42"},
        headers=headers,
    )
    assert response.status_code == 200
    db_session.expire_all()
    assert db_session.get(Incident, recent.id).str_reference == "NFIU-42"


def test_retention_five_year_floor():
    from app.core.retention import RetentionViolation, assert_deletable, is_within_retention_period

    assert is_within_retention_period(datetime.now(timezone.utc) - timedelta(days=30))
    assert not is_within_retention_period(datetime.now(timezone.utc) - timedelta(days=365 * 6))
    with pytest.raises(RetentionViolation):
        assert_deletable(datetime.now(timezone.utc) - timedelta(days=30), "incident")


def test_reset_is_disabled_in_production(client, db_session, monkeypatch):
    from app.core.config import settings

    _, headers = _authenticated_user(client, db_session, "admin", "reset")
    monkeypatch.setattr(settings, "environment", "production")
    response = client.delete("/incidents/reset", headers=headers)
    assert response.status_code == 403
