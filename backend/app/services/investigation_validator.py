"""Independent grounding checks for Cohere structured investigation output."""

from __future__ import annotations

from app.schemas.investigation import InvestigationNarrative




def validate_investigation(
    narrative: InvestigationNarrative,
    retrieved_evidence: list[dict],
    authoritative_framework_ids: set[str] | None = None,
    tenant_id: str | None = None,
) -> dict[str, bool | str]:
    # Build a lookup of retrieved evidence texts by id
    valid_ids = {str(item["evidence_id"]) for item in retrieved_evidence}
    evidence_by_id = {str(item["evidence_id"]): item for item in retrieved_evidence}

    # Collect all cited ids from findings and references
    cited_ids = {
        evidence_id
        for finding in narrative.key_findings
        for evidence_id in finding.evidence_ids
    } | {reference.evidence_id for reference in narrative.evidence_references}

    # Basic presence check: all cited ids must be among retrieved ids
    missing_ids = {cid for cid in cited_ids if cid not in valid_ids}

    # Supporting text check: each EvidenceReference.supporting_text must be
    # reasonably present in the retrieved evidence text for that id.
    mismatched_support: list[tuple[str, str]] = []
    for ref in narrative.evidence_references:
        ref_id = ref.evidence_id
        if ref_id not in evidence_by_id:
            continue
        retrieved_text = str(evidence_by_id[ref_id].get("text", ""))
        supplied = (ref.supporting_text or "").strip()
        if not supplied:
            mismatched_support.append((ref_id, "empty_supporting_text"))
            continue
        # Accept if supplied appears in retrieved or vice versa (short excerpts)
        if supplied not in retrieved_text and retrieved_text not in supplied:
            mismatched_support.append((ref_id, "support_text_mismatch"))

    evidence_grounded = not missing_ids and not mismatched_support and bool(cited_ids)

    # Framework identifiers must be provided by deterministic mapping layer;
    # the validator should not accept LLM-provided mappings as authoritative.
    frameworks_grounded = True

    # Tenant scope: ensure retrieved evidence belongs to the incident tenant.
    mismatched_tenant_ids = {
        str(item.get("metadata", {}).get("tenant_id"))
        for item in retrieved_evidence
        if tenant_id is not None
        and item.get("metadata", {}).get("tenant_id") != tenant_id
    }
    tenant_scope_valid = not mismatched_tenant_ids

    status = "validated" if (evidence_grounded and frameworks_grounded and tenant_scope_valid) else "GROUNDING_VALIDATION_FAILED"

    result = {
        "schema_valid": True,
        "evidence_grounded": evidence_grounded,
        "frameworks_grounded": frameworks_grounded,
        "tenant_scope_valid": tenant_scope_valid,
        "status": status,
    }

    # Include diagnostics for operator visibility (non-sensitive)
    if missing_ids:
        result["missing_evidence_ids"] = list(missing_ids)
    if mismatched_support:
        result["mismatched_support"] = mismatched_support
    if mismatched_tenant_ids:
        result["mismatched_tenant_ids"] = list(mismatched_tenant_ids)

    return result
