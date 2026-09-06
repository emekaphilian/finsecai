"""Read-only tenant provenance report.

Usage:
  PYTHONPATH=backend python backend/scripts/classify_tenants.py
  PYTHONPATH=backend python backend/scripts/classify_tenants.py --json

This script never updates tenant or business data.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

from sqlalchemy import text

from app.db.session import engine


def classify(name: str, description: str) -> tuple[str, str]:
    name_lower = name.lower()
    description_lower = description.lower()
    if name_lower == "acme corp":
        return "LEGITIMATE_DEMO", "canonical Acme demo tenant"
    if "benchmark" in description_lower:
        return "BENCHMARK", "tenant description identifies benchmark data"
    if "diagnostic" in name_lower or name_lower.startswith("diag-"):
        return "DIAGNOSTIC", "tenant name identifies diagnostic data"
    return "UNKNOWN", "no deterministic repository evidence"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    tables = {
        row[0]
        for row in engine.connect().execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
    }
    required = {"tenants", "users", "incidents", "evidence_chunks", "report_jobs", "audit_events", "ml_prediction_audit"}
    missing = required - tables
    if missing:
        raise RuntimeError(f"Required tables are missing: {sorted(missing)}")

    with engine.connect() as connection:
        tenant_columns = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'tenants'"
                )
            )
        }

    optional_columns = {
        column: f"t.{column}" if column in tenant_columns else f"NULL AS {column}"
        for column in ("tenant_type", "provenance", "status", "created_at", "updated_at")
    }
    query = text(
        f"""
        SELECT t.id, t.name, t.description,
               {optional_columns['tenant_type']},
               {optional_columns['provenance']},
               {optional_columns['status']},
               {optional_columns['created_at']},
               {optional_columns['updated_at']},
               count(DISTINCT u.id) AS user_count,
               count(DISTINCT i.id) AS incident_count,
               count(DISTINCT e.id) AS evidence_count,
               count(DISTINCT r.id) AS report_job_count,
               count(DISTINCT m.id) AS ml_audit_count,
               count(DISTINCT a.id) AS audit_count
        FROM tenants t
        LEFT JOIN users u ON u.tenant_id = t.id
        LEFT JOIN incidents i ON i.tenant_id = t.id
        LEFT JOIN evidence_chunks e ON e.tenant_id = t.id
        LEFT JOIN report_jobs r ON r.tenant_id = t.id
        LEFT JOIN ml_prediction_audit m ON m.tenant_id = t.id
        LEFT JOIN audit_events a ON a.tenant_id = t.id
        GROUP BY t.id, t.name, t.description
        ORDER BY t.name
        """
    )
    with engine.connect() as connection:
        rows = []
        for row in connection.execute(query).mappings():
            classification, evidence = classify(row["name"], row["description"] or "")
            item = {**dict(row), "classification": classification, "provenance_evidence": evidence}
            if item["provenance"] is None:
                item["provenance"] = classification
            if item["tenant_type"] is None:
                item["tenant_type"] = "NOT_MIGRATED"
            if item["status"] is None:
                item["status"] = "NOT_MIGRATED"
            rows.append(item)

    if args.as_json:
        print(json.dumps(rows, indent=2, default=str))
    else:
        print("tenant_id | tenant_name | tenant_type | status | provenance | classification | users | incidents | evidence | report_jobs | ml_audits | audits | evidence")
        for row in rows:
            print(
                f"{row['id']} | {row['name']} | {row['tenant_type']} | {row['status']} | {row['provenance']} | {row['classification']} | "
                f"{row['user_count']} | {row['incident_count']} | {row['evidence_count']} | "
                f"{row['report_job_count']} | {row['ml_audit_count']} | {row['audit_count']} | "
                f"{row['provenance_evidence']}"
            )
        print("classification_counts", dict(Counter(row["classification"] for row in rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
