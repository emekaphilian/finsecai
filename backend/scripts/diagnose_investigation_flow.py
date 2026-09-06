"""Diagnostic runner for the full investigation flow against a live DB.

Usage:
  python backend/scripts/diagnose_investigation_flow.py --tenant <TENANT_ID> --incident <INCIDENT_ID>

Prints retrieval query, semantic availability, number of retrieved chunks,
evidence ids and similarities, and validation status. Does not print secrets.
"""

from __future__ import annotations

import argparse
import json
from app.db.session import SessionLocal
from app.db.models import Incident
from app.services.investigation_context import build_investigation_query
from app.services.evidence_retrieval import semantic_rag_available, retrieve_relevant_evidence
from app.services.investigation_validator import validate_investigation
from app.services.cohere_investigation import generate_investigation


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tenant", required=True)
    p.add_argument("--incident", required=True)
    return p.parse_args()


def main():
    args = _parse_args()
    session = SessionLocal()
    try:
        incident = session.query(Incident).filter(Incident.id == args.incident, Incident.tenant_id == args.tenant).first()
        if not incident:
            print("Incident not found")
            return 2

        audit = None
        query = build_investigation_query(incident, audit)
        print("incident:", incident.id)
        print("tenant:", incident.tenant_id)
        print("retrieval_query:", query)
        available = semantic_rag_available(session)
        print("semantic_rag_available:", available)

        evidence = retrieve_relevant_evidence(session, incident.tenant_id, query, top_k=5)
        print("retrieved_count:", len(evidence))
        print("evidence_ids:", [e.get("evidence_id") for e in evidence])
        print("similarities:", [e.get("similarity") for e in evidence])

        # Build a minimal controlled context for LLM generation
        safe_evidence = [ {**e, "text": e.get("text", "")[:800]} for e in evidence ]

        try:
            narrative = generate_investigation({"incident": {"id": str(incident.id)}, "retrieved_evidence": safe_evidence})
            validation = validate_investigation(narrative, safe_evidence)
            print("validation:", json.dumps(validation, indent=2))
        except Exception as exc:
            print("LLM generation failed:", exc)

        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
