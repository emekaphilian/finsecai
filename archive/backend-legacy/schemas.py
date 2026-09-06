from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    tenant_id: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    tenant_id: str

    class Config:
        from_attributes = True


class IncidentOut(BaseModel):
    id: str
    user_id: str
    amount: float
    transaction_type: str
    device_id: str
    risk_score: float
    anomaly_score: float
    created_at: datetime
    confidence: float | None = None
    evidence_coverage: float | None = None
    explanation: str | None = None
    limitations: str | None = None
    governance_flags: str | None = None
    mitre_techniques: str | None = None
    nist_controls: str | None = None

    class Config:
        from_attributes = True


class FeedbackIn(BaseModel):
    label: str  # false_positive | true_positive


class AnalyticsSummary(BaseModel):
    total_incidents: int
    analyzed_count: int
    avg_risk: float
    avg_confidence: float
    high_risk_count: int
    governance_flags_count: int


class PrecisionRecall(BaseModel):
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


class DriftResult(BaseModel):
    drift_score: float
    mean_shift: float
    status: str


class CopilotQuery(BaseModel):
    query: str
