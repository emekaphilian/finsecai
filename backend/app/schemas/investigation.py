from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class EvidenceItem(BaseModel):
    type: Literal["direct", "retrieved", "similar_incident", "missing"]
    source: str
    summary: str
    confidence: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskContributor(BaseModel):
    label: str
    detail: str
    confidence: float = 0.0


class ConfidenceFactor(BaseModel):
    label: str
    positive: bool
    explanation: str


class EvidenceProvenance(BaseModel):
    derived_from: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    reasoning: str = ""


class FrameworkMapping(BaseModel):
    id: str
    name: str
    rationale: str
    confidence: float = 0.0
    derived_from: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    source: str = "rule_engine"
    # These fields are a report contract. Consumers must display them rather
    # than re-deciding whether a framework association is a finding.
    status: Literal["evidence_backed", "candidate"] = "candidate"
    basis: str = "risk-tier fallback"


class AnomalyFinding(BaseModel):
    """A persisted, display-safe investigative finding."""

    finding: str
    severity: Literal["low", "medium", "high", "critical"]
    observed_signal: str
    rationale: str
    supporting_evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class RiskAssessment(BaseModel):
    fraud_score: float = 0.0
    aml_score: float = 0.0
    insider_score: float = 0.0
    overall_confidence: float = 0.0
    score_contributions: dict[str, float] = Field(default_factory=dict)
    positive_factors: list[str] = Field(default_factory=list)
    negative_factors: list[str] = Field(default_factory=list)


class InvestigationContext(BaseModel):
    incident_id: str
    incident_timestamp: str | None = None
    severity: str = "medium"
    source: str = "unknown"
    user_id: str | None = None
    amount: float | None = None
    currency: str = "USD"
    transaction_type: str | None = None
    device_id: str | None = None
    geo: str | None = None
    risk_score: float | None = None
    anomaly_score: float | None = None
    fraud_score: float | None = None
    insider_score: float | None = None
    aml_score: float | None = None
    risk_contributors: list[RiskContributor] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    candidate_frameworks: dict[str, list[str]] = Field(default_factory=dict)
    required_output: str = "summarize the incident, explain risk, map to frameworks, and recommend actions"


class InvestigationResult(BaseModel):
    version: str = "v2"
    generated_at: str | None = None
    prompt_version: str = "investigation-enrichment-v1"
    executive_summary: str = ""
    incident_classification: str = ""
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)
    # Direct incident/model signals are recorded separately from retrieved
    # evidence chunks so the report can make the distinction explicit.
    structured_evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    indicators_of_compromise: list[str] = Field(default_factory=list)
    attack_narrative: str = ""
    confidence: float = 0.0
    confidence_factors: list[ConfidenceFactor] = Field(default_factory=list)
    findings: list[AnomalyFinding] = Field(default_factory=list)
    risk_rationale: list[str] = Field(default_factory=list)
    mitre: list[FrameworkMapping] = Field(default_factory=list)
    nist: list[FrameworkMapping] = Field(default_factory=list)
    iso27001: list[FrameworkMapping] = Field(default_factory=list)
    pci_dss: list[FrameworkMapping] = Field(default_factory=list)
    ffiec: list[FrameworkMapping] = Field(default_factory=list)
    iocs: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class EvidenceReference(BaseModel):
    evidence_id: str
    relevance: str
    supporting_text: str


class InvestigationFinding(BaseModel):
    finding: str
    severity: Literal["low", "medium", "high", "critical"]
    evidence_ids: list[str] = Field(default_factory=list)


class InvestigationNarrative(BaseModel):
    summary: str
    risk_assessment: str
    key_findings: list[InvestigationFinding] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence: float = 0.0

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        return value
