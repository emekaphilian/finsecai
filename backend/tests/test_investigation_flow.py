import asyncio

from app.services.evidence_retrieval import retrieve_relevant_evidence, semantic_rag_available
from app.services.investigation_validator import validate_investigation
from app.schemas.investigation import InvestigationNarrative, EvidenceReference, InvestigationFinding


def test_retrieve_relevant_evidence_non_postgres_returns_empty(db_session, monkeypatch):
    # Force non-postgres environment
    monkeypatch.setattr("app.services.evidence_retrieval.semantic_rag_available", lambda _db: False)

    rows = retrieve_relevant_evidence(db_session, "tenant-x", "some query", top_k=3)
    assert rows == []


def test_validate_investigation_passes_for_valid_citation():
    retrieved = [{"evidence_id": "e1", "text": "Suspicious transfer to offshore beneficiary"}]

    narrative = InvestigationNarrative(
        summary="a",
        risk_assessment="r",
        key_findings=[InvestigationFinding(finding="f", severity="high", evidence_ids=["e1"])],
        recommended_actions=[],
        evidence_references=[EvidenceReference(evidence_id="e1", relevance="high", supporting_text="Suspicious transfer")],
        limitations=[],
        confidence=0.8,
    )

    result = validate_investigation(narrative, retrieved)
    assert result["status"] == "validated"


def test_validate_investigation_fails_for_missing_or_mismatched():
    retrieved = [{"evidence_id": "e1", "text": "Full retrieved text here"}]

    # Missing id
    narrative_missing = InvestigationNarrative(
        summary="a",
        risk_assessment="r",
        key_findings=[InvestigationFinding(finding="f", severity="high", evidence_ids=["e2"])],
        recommended_actions=[],
        evidence_references=[],
        limitations=[],
        confidence=0.5,
    )
    res_missing = validate_investigation(narrative_missing, retrieved)
    assert res_missing["status"] == "GROUNDING_VALIDATION_FAILED"

    # Mismatched support text
    narrative_mismatch = InvestigationNarrative(
        summary="a",
        risk_assessment="r",
        key_findings=[],
        recommended_actions=[],
        evidence_references=[EvidenceReference(evidence_id="e1", relevance="low", supporting_text="unrelated text")],
        limitations=[],
        confidence=0.4,
    )
    res_mismatch = validate_investigation(narrative_mismatch, retrieved)
    assert res_mismatch["status"] == "GROUNDING_VALIDATION_FAILED"


def test_validate_investigation_rejects_cross_tenant_evidence():
    retrieved = [
        {
            "evidence_id": "e1",
            "text": "Suspicious transfer",
            "metadata": {"tenant_id": "tenant-b"},
        }
    ]
    narrative = InvestigationNarrative(
        summary="a",
        risk_assessment="r",
        key_findings=[InvestigationFinding(finding="f", severity="high", evidence_ids=["e1"])],
        evidence_references=[EvidenceReference(evidence_id="e1", relevance="high", supporting_text="Suspicious transfer")],
        confidence=0.8,
    )

    result = validate_investigation(narrative, retrieved, tenant_id="tenant-a")

    assert result["status"] == "GROUNDING_VALIDATION_FAILED"
    assert result["tenant_scope_valid"] is False
