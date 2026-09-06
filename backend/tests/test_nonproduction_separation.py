import json

import pytest

from scripts.nonproduction_separation import (
    ALL_TRANSFER_TABLES,
    EXPECTED_NONPRODUCTION_TENANTS,
    SeparationToolError,
    build_manifest,
    build_transfer_plan,
    tenant_ids,
    validate_target,
)
from scripts.nonproduction_separation import (
    _connect_for_validation,
    _count_query,
    _expected_count,
    _key_query,
    _target_is_empty,
    _validate_transfer_urls,
)


class Cursor:
    def __init__(self, tenant_ids, acme_present=False):
        self.tenant_ids = tenant_ids
        self.acme_present = acme_present
        self.result = None

    def execute(self, query):
        if query.startswith("SELECT id, name, description FROM tenants"):
            self.result = [
                (
                    tenant_id,
                    "Benchmark-" + tenant_id.removeprefix("bench-")
                    if tenant_id.startswith("bench-")
                    else "Diagnostic-" + tenant_id.removeprefix("diag-"),
                    "benchmark" if tenant_id.startswith("bench-") else "diagnostic",
                )
                for tenant_id in sorted(self.tenant_ids)
            ]
        elif "SELECT count(*) FROM tenants WHERE lower(name)" in query:
            self.result = [(1 if self.acme_present else 0,)]
        elif "SELECT count(*) FROM incidents i LEFT JOIN tenants" in query:
            self.result = [(0,)]
        elif "SELECT count(*) FROM ml_prediction_audit" in query:
            self.result = [(0,)]
        elif "SELECT count(*) FROM authoritative_labels" in query:
            self.result = [(0,)]
        elif "SELECT count(*) FROM suspicious_transaction_reports" in query:
            self.result = [(0,)]
        else:
            self.result = [(0,)]

    def fetchall(self):
        return self.result

    def fetchone(self):
        return self.result[0]

    def close(self):
        pass


class Connection:
    def __init__(self, tenant_ids, acme_present=False):
        self.cursor_value = Cursor(tenant_ids, acme_present=acme_present)

    def cursor(self):
        return self.cursor_value


class EmptyCheckCursor:
    def __init__(self, counts):
        self.counts = iter(counts)
        self.value = None

    def execute(self, _query):
        self.value = next(self.counts)

    def fetchone(self):
        return (self.value,)

    def close(self):
        pass


class EmptyCheckConnection:
    def __init__(self, counts):
        self.value = EmptyCheckCursor(counts)

    def cursor(self):
        return self.value


def rows():
    return [
        {"id": f"bench-{index:02d}", "name": f"Benchmark-{index:02d}", "description": "benchmark"}
        for index in range(44)
    ] + [
        {"id": f"diag-{index:02d}", "name": f"Diagnostic-{index:02d}", "description": "diagnostic"}
        for index in range(11)
    ] + [{"id": "acme-id", "name": "Acme Corp", "description": "Default demo tenant"}]


def test_manifest_selects_exactly_55_and_excludes_acme():
    manifest = build_manifest(rows())
    assert manifest["tenant_count"] == EXPECTED_NONPRODUCTION_TENANTS
    assert len(tenant_ids(manifest)) == 55
    assert "acme-id" not in tenant_ids(manifest)
    assert {item["classification"] for item in manifest["tenants"]} == {"BENCHMARK", "DIAGNOSTIC"}


def test_manifest_generation_is_deterministic():
    assert build_manifest(rows()) == build_manifest(list(reversed(rows())))


def test_manifest_rejects_unexpected_tenant_set():
    incomplete = rows()[:43] + rows()[44:]
    with pytest.raises(SeparationToolError, match="found 54"):
        build_manifest(incomplete)


def test_transfer_plan_uses_explicit_uuids_and_preserves_ids(tmp_path):
    manifest = build_manifest(rows())
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    plan = build_transfer_plan(str(manifest_path), "source-url", "target-url")
    assert "WHERE name <> 'Acme Corp'" not in plan
    assert "nonproduction_separation.py transfer" in plan
    assert "source-url" in plan
    assert "target-url" in plan
    assert "CSV" not in plan


def test_validator_accepts_exact_manifest_target():
    manifest = build_manifest(rows())
    result = validate_target(Connection(set(tenant_ids(manifest))), manifest)
    assert result["passed"] is True
    assert result["checks"]["tenant_uuid_equality"] is True


def test_validator_rejects_acme_or_unexpected_target_tenant():
    manifest = build_manifest(rows())
    target_ids = set(tenant_ids(manifest)) | {"acme-id", "unexpected-id"}
    result = validate_target(Connection(target_ids), manifest)
    assert result["passed"] is False
    assert result["checks"]["acme_absent"] is True
    assert result["checks"]["unexpected_tenants_absent"] is False
    assert result["checks"]["tenant_uuid_equality"] is False

    acme_result = validate_target(
        Connection(set(tenant_ids(manifest)), acme_present=True), manifest
    )
    assert acme_result["checks"]["acme_absent"] is False


def test_validator_rejects_application_database_name():
    with pytest.raises(SeparationToolError):
        _connect_for_validation("postgresql+psycopg2://different-host/finsecai")


def test_transfer_url_guard_rejects_production_and_noncanonical_targets():
    with pytest.raises(SeparationToolError):
        _validate_transfer_urls("source/finsecai", "target/finsecai")
    with pytest.raises(SeparationToolError):
        _validate_transfer_urls("source/finsecai", "target/other")


def test_transfer_dependency_order_and_indirect_queries():
    assert ALL_TRANSFER_TABLES == (
        "tenants",
        "users",
        "incidents",
        "evidence_chunks",
        "report_jobs",
        "dataset_versions",
        "ml_prediction_audit",
        "authoritative_labels",
        "feedback",
        "suspicious_transaction_reports",
        "model_versions",
        "evaluation_runs",
        "audit_events",
    )
    from scripts.nonproduction_separation import TRANSFER_QUERIES

    assert "JOIN incidents" in TRANSFER_QUERIES["feedback"]
    assert "JOIN dataset_versions" in TRANSFER_QUERIES["model_versions"]
    assert "JOIN dataset_versions" in TRANSFER_QUERIES["evaluation_runs"]


def test_transfer_requires_empty_target_by_default():
    assert _target_is_empty(EmptyCheckConnection([0] * len(ALL_TRANSFER_TABLES))) is True
    assert _target_is_empty(EmptyCheckConnection([0, 1])) is False


def test_validator_uses_root_tenant_id_and_dependent_tenant_relationships():
    ids = ("tenant-a",)
    assert "FROM tenants WHERE id = ANY" in _count_query("tenants", ids)
    assert "tenant_id" not in _count_query("tenants", ids)
    assert "FROM tenants WHERE id = ANY" in _key_query("tenants", ids)
    assert "tenant_id" not in _key_query("tenants", ids)
    assert "FROM incidents WHERE tenant_id = ANY" in _count_query("incidents", ids)
    assert "FROM incidents WHERE tenant_id = ANY" in _key_query("incidents", ids)


def test_expected_tenant_count_comes_from_manifest_uuid_boundary():
    manifest = build_manifest(rows())
    assert _expected_count("tenants", manifest, tenant_ids(manifest)) == 55
    assert _expected_count("evidence_chunks", manifest, tenant_ids(manifest)) == 0

    manifest_without_tenant_count = {
        **manifest,
        "tenants": [
            {key: value for key, value in item.items() if key != "expected_counts"}
            for item in manifest["tenants"]
        ],
    }
    assert _expected_count(
        "tenants", manifest_without_tenant_count, tenant_ids(manifest_without_tenant_count)
    ) == 55
