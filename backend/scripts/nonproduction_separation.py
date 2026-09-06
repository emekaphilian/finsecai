"""Manifest-driven, non-destructive separation tooling.

This module does not execute transfers. It generates reviewed PostgreSQL
commands and validates an already-populated isolated database. The source
boundary is the explicit tenant UUID manifest, never a tenant-name predicate.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import create_engine, text

from app.core.config import settings

MANIFEST_VERSION = "phase3b-v1"
EXPECTED_NONPRODUCTION_TENANTS = 55
ACME_NAME = "Acme Corp"

TENANT_TABLES = (
    "tenants",
    "users",
    "incidents",
    "evidence_chunks",
    "report_jobs",
    "dataset_versions",
)
INDIRECT_TABLES = (
    "ml_prediction_audit",
    "authoritative_labels",
    "feedback",
    "suspicious_transaction_reports",
    "model_versions",
    "evaluation_runs",
    "audit_events",
)
ALL_TRANSFER_TABLES = TENANT_TABLES + INDIRECT_TABLES


class SeparationToolError(RuntimeError):
    pass


def classify_tenant(name: str, description: str) -> tuple[str, str] | None:
    """Return the established disposition classification for a tenant."""
    name_lower = name.lower()
    description_lower = description.lower()
    if name_lower == ACME_NAME.lower():
        return None
    if "benchmark" in description_lower:
        return "BENCHMARK", "tenant description identifies benchmark data"
    if "diagnostic" in name_lower or name_lower.startswith("diag-"):
        return "DIAGNOSTIC", "tenant name identifies diagnostic data"
    return None


def build_manifest(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a deterministic UUID manifest from classified tenant rows."""
    entries = []
    for row in rows:
        classification = classify_tenant(str(row["name"]), str(row.get("description") or ""))
        if classification is None:
            continue
        category, evidence = classification
        entries.append(
            {
                "tenant_id": str(row["id"]),
                "tenant_name": str(row["name"]),
                "classification": category,
                "classification_evidence": evidence,
                "expected_counts": {
                    table: int(row.get(f"{table}_count", 0))
                    for table in ALL_TRANSFER_TABLES
                    if f"{table}_count" in row
                },
                "expected_keys": {
                    table: [str(key) for key in row.get(f"{table}_keys", [])]
                    for table in ALL_TRANSFER_TABLES
                    if row.get(f"{table}_keys") is not None
                },
            }
        )

    entries.sort(key=lambda item: item["tenant_id"])
    if len(entries) != EXPECTED_NONPRODUCTION_TENANTS:
        raise SeparationToolError(
            f"Expected {EXPECTED_NONPRODUCTION_TENANTS} classified tenants, found {len(entries)}"
        )
    if len({entry["tenant_id"] for entry in entries}) != len(entries):
        raise SeparationToolError("Manifest contains duplicate tenant UUIDs")
    if any(entry["tenant_name"].lower() == ACME_NAME.lower() for entry in entries):
        raise SeparationToolError("Manifest must not contain Acme Corp")

    return {
        "manifest_version": MANIFEST_VERSION,
        "source_database": "finsecai",
        "target_database": "finsecai_isolated",
        "tenant_count": len(entries),
        "tenants": entries,
    }


def tenant_ids(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    ids = tuple(str(item["tenant_id"]) for item in manifest["tenants"])
    if len(ids) != EXPECTED_NONPRODUCTION_TENANTS or len(set(ids)) != len(ids):
        raise SeparationToolError("Manifest must contain exactly 55 unique tenant UUIDs")
    return ids


def _sql_uuid_array(ids: tuple[str, ...]) -> str:
    escaped = ", ".join("'" + tenant_id.replace("'", "''") + "'" for tenant_id in ids)
    return f"ARRAY[{escaped}]::varchar[]"


def build_transfer_plan(manifest_path: str, source_database_url: str, target_database_url: str) -> str:
    """Generate the manual binary-COPY transfer command without executing it."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    tenant_ids(manifest)
    return (
        "# REVIEW ONLY: this command is not executed by the plan command.\n"
        "py -3.11 backend/scripts/nonproduction_separation.py transfer "
        f"--manifest \"{manifest_path}\" "
        f"--source-database-url \"{source_database_url}\" "
        f"--target-database-url \"{target_database_url}\"\n"
    )


def _count_query(table: str, ids: tuple[str, ...]) -> str:
    id_array = _sql_uuid_array(ids)
    if table == "tenants":
        return f"SELECT count(*) FROM tenants WHERE id = ANY({id_array})"
    if table == "feedback":
        return f"SELECT count(*) FROM feedback f JOIN incidents i ON i.id=f.incident_id WHERE i.tenant_id = ANY({id_array})"
    if table == "model_versions":
        return f"SELECT count(*) FROM model_versions m JOIN dataset_versions d ON d.id=m.dataset_version_id WHERE d.tenant_id = ANY({id_array})"
    if table == "evaluation_runs":
        return f"SELECT count(*) FROM evaluation_runs e JOIN dataset_versions d ON d.id=e.dataset_version_id WHERE d.tenant_id = ANY({id_array})"
    return f"SELECT count(*) FROM {table} WHERE tenant_id = ANY({id_array})"


def _expected_count(table: str, manifest: Mapping[str, Any], ids: tuple[str, ...]) -> int:
    """Return the expected count using the same boundary as transfer selection."""
    if table == "tenants":
        return len(ids)
    return sum(
        int(item.get("expected_counts", {}).get(table, 0))
        for item in manifest["tenants"]
    )


def _key_query(table: str, ids: tuple[str, ...]) -> str:
    id_array = _sql_uuid_array(ids)
    if table == "tenants":
        return f"SELECT id FROM tenants WHERE id = ANY({id_array}) ORDER BY id"
    if table == "feedback":
        return f"SELECT f.id FROM feedback f JOIN incidents i ON i.id=f.incident_id WHERE i.tenant_id = ANY({id_array}) ORDER BY f.id"
    if table == "model_versions":
        return f"SELECT m.id FROM model_versions m JOIN dataset_versions d ON d.id=m.dataset_version_id WHERE d.tenant_id = ANY({id_array}) ORDER BY m.id"
    if table == "evaluation_runs":
        return f"SELECT e.model_version_id || ':' || e.dataset_version_id FROM evaluation_runs e JOIN dataset_versions d ON d.id=e.dataset_version_id WHERE d.tenant_id = ANY({id_array}) ORDER BY 1"
    return f"SELECT id FROM {table} WHERE tenant_id = ANY({id_array}) ORDER BY id"


TRANSFER_QUERIES = {
    "tenants": "SELECT * FROM tenants WHERE id = ANY(%s) ORDER BY id",
    "users": "SELECT * FROM users WHERE tenant_id = ANY(%s) ORDER BY id",
    "incidents": "SELECT * FROM incidents WHERE tenant_id = ANY(%s) ORDER BY id",
    "evidence_chunks": "SELECT * FROM evidence_chunks WHERE tenant_id = ANY(%s) ORDER BY id",
    "report_jobs": "SELECT * FROM report_jobs WHERE tenant_id = ANY(%s) ORDER BY id",
    "dataset_versions": "SELECT * FROM dataset_versions WHERE tenant_id = ANY(%s) ORDER BY id",
    "ml_prediction_audit": "SELECT * FROM ml_prediction_audit WHERE tenant_id = ANY(%s) ORDER BY id",
    "authoritative_labels": "SELECT * FROM authoritative_labels WHERE tenant_id = ANY(%s) ORDER BY id",
    "feedback": "SELECT f.* FROM feedback f JOIN incidents i ON i.id=f.incident_id WHERE i.tenant_id = ANY(%s) ORDER BY f.id",
    "suspicious_transaction_reports": "SELECT * FROM suspicious_transaction_reports WHERE tenant_id = ANY(%s) ORDER BY id",
    "model_versions": "SELECT m.* FROM model_versions m JOIN dataset_versions d ON d.id=m.dataset_version_id WHERE d.tenant_id = ANY(%s) ORDER BY m.id",
    "evaluation_runs": "SELECT e.* FROM evaluation_runs e JOIN dataset_versions d ON d.id=e.dataset_version_id WHERE d.tenant_id = ANY(%s) ORDER BY e.model_version_id, e.dataset_version_id",
    "audit_events": "SELECT * FROM audit_events WHERE tenant_id = ANY(%s) ORDER BY id",
}


def _schema_signature(connection: Any, tables: tuple[str, ...]) -> dict[str, tuple[tuple[str, str, str], ...]]:
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT table_name,column_name,data_type,is_nullable "
            "FROM information_schema.columns WHERE table_schema='public' "
            "AND table_name = ANY(%s) ORDER BY table_name,ordinal_position",
            (list(tables),),
        )
        signature: dict[str, list[tuple[str, str, str]]] = {}
        for table, column, data_type, nullable in cursor.fetchall():
            signature.setdefault(table, []).append((column, data_type, nullable))
        return {table: tuple(signature.get(table, ())) for table in tables}
    finally:
        cursor.close()


def _connection_identity(connection: Any) -> tuple[str, str | None, int | None]:
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT current_database(), inet_server_addr()::text, inet_server_port()")
        database, host, port = cursor.fetchone()
        return str(database), host, int(port) if port is not None else None
    finally:
        cursor.close()


def _database_name(database_url: str) -> str:
    return urlsplit(database_url).path.rsplit("/", 1)[-1]


def _validate_transfer_urls(source_database_url: str, target_database_url: str) -> None:
    if not source_database_url or not target_database_url:
        raise SeparationToolError("Source and target database URLs are required")
    source_name = _database_name(source_database_url)
    target_name = _database_name(target_database_url)
    if target_name == "finsecai":
        raise SeparationToolError("Refusing production database as transfer target")
    if source_name == target_name == "finsecai":
        raise SeparationToolError("Source and target resolve to the production database")
    if target_name != "finsecai_isolated":
        raise SeparationToolError("Transfer target must be finsecai_isolated")


def _target_is_empty(connection: Any) -> bool:
    cursor = connection.cursor()
    try:
        for table in ALL_TRANSFER_TABLES:
            cursor.execute(f"SELECT count(*) FROM {table}")
            if cursor.fetchone()[0]:
                return False
        return True
    finally:
        cursor.close()


def _verify_source_manifest(connection: Any, ids: tuple[str, ...]) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id FROM tenants WHERE id = ANY(%s)", (list(ids),))
        found = {str(row[0]) for row in cursor.fetchall()}
    finally:
        cursor.close()
    if found != set(ids):
        missing = sorted(set(ids) - found)
        raise SeparationToolError(f"Source manifest UUIDs missing from source: {missing}")


def _copy_binary(source: Any, target: Any, table: str, ids: tuple[str, ...]) -> None:
    """Copy one filtered table through PostgreSQL's binary COPY protocol."""
    source_cursor = source.cursor()
    target_cursor = target.cursor()
    try:
        source_cursor.execute(TRANSFER_QUERIES[table] + " LIMIT 0", (list(ids),))
        columns = [description[0] for description in source_cursor.description]
        quoted_columns = ", ".join('"' + column.replace('"', '""') + '"' for column in columns)
        source_sql = TRANSFER_QUERIES[table].replace("SELECT *", f"SELECT {quoted_columns}")
        with tempfile.SpooledTemporaryFile(max_size=16 * 1024 * 1024, mode="w+b") as stream:
            source_sql = source_cursor.mogrify(source_sql, (list(ids),)).decode("utf-8")
            source_cursor.copy_expert(
                f"COPY ({source_sql}) TO STDOUT WITH (FORMAT BINARY)",
                stream,
            )
            stream.seek(0)
            target_cursor.copy_expert(
                f"COPY {table} ({quoted_columns}) FROM STDIN WITH (FORMAT BINARY)",
                stream,
            )
    finally:
        source_cursor.close()
        target_cursor.close()


def transfer(manifest: Mapping[str, Any], source_database_url: str, target_database_url: str, allow_existing_target: bool = False) -> dict[str, Any]:
    """Transfer the immutable manifest boundary into a target transaction."""
    ids = tenant_ids(manifest)
    _validate_transfer_urls(source_database_url, target_database_url)
    source_engine = create_engine(source_database_url, pool_pre_ping=True)
    target_engine = create_engine(target_database_url, pool_pre_ping=True)
    source = source_engine.raw_connection()
    target = target_engine.raw_connection()
    try:
        source_identity = _connection_identity(source)
        target_identity = _connection_identity(target)
        if source_identity == target_identity or target_identity[0] == "finsecai":
            raise SeparationToolError("Source and target resolve to the same or production database")
        source.rollback()
        source_cursor = source.cursor()
        source_cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        source_cursor.close()
        _verify_source_manifest(source, ids)
        if _schema_signature(source, ALL_TRANSFER_TABLES) != _schema_signature(target, ALL_TRANSFER_TABLES):
            raise SeparationToolError("Source and target transfer schemas do not match")
        if not allow_existing_target and not _target_is_empty(target):
            raise SeparationToolError("Target is not empty; use --allow-existing-target explicitly")

        target.rollback()
        target_cursor = target.cursor()
        target_cursor.execute("BEGIN")
        target_cursor.close()
        for table in ALL_TRANSFER_TABLES:
            _copy_binary(source, target, table, ids)
        result = validate_target(target, manifest)
        if not result["passed"]:
            raise SeparationToolError(f"Target validation failed before commit: {result}")
        target.commit()
        return result
    except Exception:
        target.rollback()
        raise
    finally:
        source.close()
        target.close()
        source_engine.dispose()
        target_engine.dispose()


def validate_target(connection: Any, manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Read-only validation of UUID, count, and cross-tenant invariants."""
    ids = tenant_ids(manifest)
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id, name, description FROM tenants ORDER BY id")
        target_rows = cursor.fetchall()
        actual_ids = {str(row[0]) for row in target_rows}
        expected_ids = set(ids)
        expected_by_id = {str(item["tenant_id"]): item for item in manifest["tenants"]}
        classification_matches = all(
            tenant_id in expected_by_id
            and str(name) == expected_by_id[tenant_id]["tenant_name"]
            for tenant_id, name, _description in target_rows
        )
        counts: dict[str, int] = {}
        actual_keys: dict[str, list[str]] = {}
        for table in ALL_TRANSFER_TABLES:
            cursor.execute(_count_query(table, ids))
            counts[table] = int(cursor.fetchone()[0])
            cursor.execute(_key_query(table, ids))
            actual_keys[table] = [str(row[0]) for row in cursor.fetchall()]
        checks = {
            "tenant_uuid_equality": actual_ids == expected_ids,
            "tenant_classification_matches": classification_matches,
            "acme_absent": _read_count(cursor, "SELECT count(*) FROM tenants WHERE lower(name) = 'acme corp'") == 0,
            "unexpected_tenants_absent": actual_ids <= expected_ids,
            "orphan_incidents_absent": _read_count(cursor, "SELECT count(*) FROM incidents i LEFT JOIN tenants t ON t.id=i.tenant_id WHERE t.id IS NULL") == 0,
            "cross_tenant_ml_absent": _read_count(cursor, "SELECT count(*) FROM ml_prediction_audit m JOIN incidents i ON i.id=m.incident_id WHERE m.tenant_id <> i.tenant_id") == 0,
            "cross_tenant_labels_absent": _read_count(cursor, "SELECT count(*) FROM authoritative_labels l JOIN incidents i ON i.id=l.incident_id WHERE l.tenant_id <> i.tenant_id") == 0,
            "cross_tenant_reports_absent": _read_count(cursor, "SELECT count(*) FROM suspicious_transaction_reports s JOIN incidents i ON i.id=s.incident_id WHERE s.tenant_id <> i.tenant_id") == 0,
        }
        expected_counts = {
            table: _expected_count(table, manifest, ids) for table in ALL_TRANSFER_TABLES
        }
        if any(item.get("expected_counts") for item in manifest["tenants"]):
            checks["per_table_counts_match"] = counts == expected_counts
        expected_keys = {
            table: sorted(
                str(key)
                for item in manifest["tenants"]
                for key in item.get("expected_keys", {}).get(table, [])
            )
            for table in ALL_TRANSFER_TABLES
        }
        if any(item.get("expected_keys") for item in manifest["tenants"]):
            checks["primary_keys_preserved"] = actual_keys == expected_keys
        return {"passed": all(checks.values()), "checks": checks, "counts": counts}
    finally:
        cursor.close()


def _read_count(cursor: Any, query: str) -> int:
    cursor.execute(query)
    return int(cursor.fetchone()[0])


def _connect_for_validation(database_url: str):
    if not database_url:
        raise SeparationToolError("A target database URL is required")
    if (
        database_url == settings.database_url
        or urlsplit(database_url).path.rsplit("/", 1)[-1] == "finsecai"
    ):
        raise SeparationToolError("Refusing to validate against the application database")
    parsed = urlsplit(database_url)
    if not parsed.scheme or not parsed.netloc:
        raise SeparationToolError("Invalid target database URL")
    return create_engine(database_url, pool_pre_ping=True).raw_connection()


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--database-url", required=True)
    manifest_parser.add_argument("--output", required=True)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--manifest", required=True)
    plan_parser.add_argument("--source-database-url", required=True)
    plan_parser.add_argument("--target-database-url", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--manifest", required=True)
    validate_parser.add_argument("--database-url", required=True)
    transfer_parser = subparsers.add_parser("transfer")
    transfer_parser.add_argument("--manifest", required=True)
    transfer_parser.add_argument("--source-database-url", required=True)
    transfer_parser.add_argument(
        "--target-database-url",
        default=os.getenv("FINSECAI_BENCHMARK_DATABASE_URL", ""),
    )
    transfer_parser.add_argument("--allow-existing-target", action="store_true")
    args = parser.parse_args()

    if args.command == "manifest":
        engine = create_engine(args.database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT t.id, t.name, t.description,
                        (SELECT count(*) FROM users u WHERE u.tenant_id=t.id) users_count,
                        (SELECT count(*) FROM incidents i WHERE i.tenant_id=t.id) incidents_count,
                        (SELECT count(*) FROM evidence_chunks e WHERE e.tenant_id=t.id) evidence_chunks_count,
                        (SELECT count(*) FROM report_jobs r WHERE r.tenant_id=t.id) report_jobs_count,
                        (SELECT count(*) FROM ml_prediction_audit m WHERE m.tenant_id=t.id) ml_prediction_audit_count,
                        (SELECT count(*) FROM authoritative_labels a WHERE a.tenant_id=t.id) authoritative_labels_count,
                        (SELECT count(*) FROM suspicious_transaction_reports s WHERE s.tenant_id=t.id) suspicious_transaction_reports_count,
                        (SELECT count(*) FROM audit_events v WHERE v.tenant_id=t.id) audit_events_count,
                        (SELECT count(*) FROM dataset_versions d WHERE d.tenant_id=t.id) dataset_versions_count,
                        (SELECT count(*) FROM feedback f JOIN incidents i ON i.id=f.incident_id WHERE i.tenant_id=t.id) feedback_count,
                        (SELECT count(*) FROM model_versions m JOIN dataset_versions d ON d.id=m.dataset_version_id WHERE d.tenant_id=t.id) model_versions_count,
                        (SELECT count(*) FROM evaluation_runs e JOIN dataset_versions d ON d.id=e.dataset_version_id WHERE d.tenant_id=t.id) evaluation_runs_count,
                        COALESCE((SELECT array_agg(u.id::text ORDER BY u.id) FROM users u WHERE u.tenant_id=t.id), ARRAY[]::text[]) users_keys,
                        ARRAY[t.id::text] tenants_keys,
                        COALESCE((SELECT array_agg(i.id::text ORDER BY i.id) FROM incidents i WHERE i.tenant_id=t.id), ARRAY[]::text[]) incidents_keys,
                        COALESCE((SELECT array_agg(e.id::text ORDER BY e.id) FROM evidence_chunks e WHERE e.tenant_id=t.id), ARRAY[]::text[]) evidence_chunks_keys,
                        COALESCE((SELECT array_agg(r.id::text ORDER BY r.id) FROM report_jobs r WHERE r.tenant_id=t.id), ARRAY[]::text[]) report_jobs_keys,
                        COALESCE((SELECT array_agg(m.id::text ORDER BY m.id) FROM ml_prediction_audit m WHERE m.tenant_id=t.id), ARRAY[]::text[]) ml_prediction_audit_keys,
                        COALESCE((SELECT array_agg(a.id::text ORDER BY a.id) FROM authoritative_labels a WHERE a.tenant_id=t.id), ARRAY[]::text[]) authoritative_labels_keys,
                        COALESCE((SELECT array_agg(s.id::text ORDER BY s.id) FROM suspicious_transaction_reports s WHERE s.tenant_id=t.id), ARRAY[]::text[]) suspicious_transaction_reports_keys,
                        COALESCE((SELECT array_agg(v.id::text ORDER BY v.id) FROM audit_events v WHERE v.tenant_id=t.id), ARRAY[]::text[]) audit_events_keys,
                        COALESCE((SELECT array_agg(d.id::text ORDER BY d.id) FROM dataset_versions d WHERE d.tenant_id=t.id), ARRAY[]::text[]) dataset_versions_keys,
                        COALESCE((SELECT array_agg(f.id::text ORDER BY f.id) FROM feedback f JOIN incidents i ON i.id=f.incident_id WHERE i.tenant_id=t.id), ARRAY[]::text[]) feedback_keys,
                        COALESCE((SELECT array_agg(m.id::text ORDER BY m.id) FROM model_versions m JOIN dataset_versions d ON d.id=m.dataset_version_id WHERE d.tenant_id=t.id), ARRAY[]::text[]) model_versions_keys,
                        COALESCE((SELECT array_agg((e.model_version_id || ':' || e.dataset_version_id) ORDER BY e.model_version_id,e.dataset_version_id) FROM evaluation_runs e JOIN dataset_versions d ON d.id=e.dataset_version_id WHERE d.tenant_id=t.id), ARRAY[]::text[]) evaluation_runs_keys
                    FROM tenants t ORDER BY t.id
                    """
                )
            ).mappings()
            manifest = build_manifest(rows)
        Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"manifest": args.output, "tenant_count": manifest["tenant_count"]}))
        return 0
    if args.command == "plan":
        print(build_transfer_plan(args.manifest, args.source_database_url, args.target_database_url))
        return 0
    if args.command == "validate":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        connection = _connect_for_validation(args.database_url)
        try:
            result = validate_target(connection, manifest)
        finally:
            connection.close()
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1
    if args.command == "transfer":
        if not args.target_database_url:
            raise SeparationToolError(
                "--target-database-url or FINSECAI_BENCHMARK_DATABASE_URL is required"
            )
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        result = transfer(
            manifest,
            args.source_database_url,
            args.target_database_url,
            allow_existing_target=args.allow_existing_target,
        )
        print(json.dumps(result, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SeparationToolError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2) from exc
