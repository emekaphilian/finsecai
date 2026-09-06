import pytest

from app.core import database_boundary
from app.db.models import TenantProvenance, TenantType


def test_provenance_vocabulary_and_business_type_are_distinct():
    assert {item.value for item in TenantProvenance} == {
        "LEGITIMATE_DEMO",
        "LEGITIMATE_CUSTOMER",
        "BENCHMARK",
        "DIAGNOSTIC",
        "TEST",
        "UNKNOWN",
    }
    assert {item.value for item in TenantType} == {"DEMO", "CUSTOMER"}


def test_benchmark_database_boundary_fails_closed(monkeypatch):
    monkeypatch.delenv("FINSECAI_BENCHMARK_DATABASE_URL", raising=False)
    with pytest.raises(database_boundary.DatabaseBoundaryError):
        database_boundary.benchmark_session_factory()


def test_benchmark_database_boundary_rejects_application_database(monkeypatch):
    from app.core.config import settings

    monkeypatch.setenv("FINSECAI_BENCHMARK_DATABASE_URL", settings.database_url)
    with pytest.raises(database_boundary.DatabaseBoundaryError):
        database_boundary.benchmark_session_factory()

    monkeypatch.setenv(
        "FINSECAI_BENCHMARK_DATABASE_URL",
        "postgresql+psycopg2://different-host/finsecai",
    )
    with pytest.raises(database_boundary.DatabaseBoundaryError):
        database_boundary.benchmark_session_factory()


def test_migration_does_not_default_existing_tenants_to_customer():
    migration = open("migrations_raw_sql/007_enterprise_tenant_provisioning.sql", encoding="utf-8").read()
    assert "tenant_type VARCHAR NULL" in migration
    assert "tenant_type VARCHAR NOT NULL DEFAULT 'CUSTOMER'" not in migration
    assert "provenance VARCHAR NOT NULL DEFAULT 'UNKNOWN'" in migration
    assert "provenance = 'BENCHMARK'" in migration
    assert "provenance = 'DIAGNOSTIC'" in migration
