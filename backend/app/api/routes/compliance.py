"""Tenant-isolated CBN/NFIU audit export and human-operated STR workflow."""

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.authorization import (
    COMPLIANCE_AUDIT_EXPORT,
    COMPLIANCE_READ,
    COMPLIANCE_STR_CREATE,
    COMPLIANCE_STR_SUBMIT,
    COMPLIANCE_STR_UPDATE,
    apply_tenant_scope,
    require_permission,
)
from app.core.config import settings
from app.db.models import (
    Incident,
    MLPredictionAudit,
    SuspiciousTransactionReport,
    User,
)
from app.db.session import get_db
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/compliance", tags=["compliance"])


def _serialize_rows(db: Session, user: User, start: datetime, end: datetime, minimum: float):
    query = (
        db.query(Incident, MLPredictionAudit)
        .outerjoin(MLPredictionAudit, MLPredictionAudit.incident_id == Incident.id)
        .filter(
            Incident.created_at >= start,
            Incident.created_at <= end,
            Incident.risk_score >= minimum,
        )
    )
    records = apply_tenant_scope(query, Incident, user).order_by(Incident.created_at.asc()).all()
    for incident, audit in records:
        factors = ""
        if audit and audit.feature_contributions:
            factors = "; ".join(
                f"{item.get('feature', 'unknown')}={item.get('value', 0):.3g} "
                f"(impact {item.get('shap', 0):+.3f})"
                for item in audit.feature_contributions[:3]
            )
        yield {
            "incident_id": incident.id,
            "created_at": incident.created_at.isoformat() if incident.created_at else "",
            "user_id": incident.user_id,
            "amount": incident.amount,
            "transaction_type": incident.transaction_type,
            "device_id": incident.device_id,
            "risk_score": incident.risk_score,
            "anomaly_score": incident.anomaly_score,
            "confidence": incident.confidence,
            "governance_flags": incident.governance_flags or "",
            "mitre_techniques": incident.mitre_techniques or "",
            "nist_controls": incident.nist_controls or "",
            "explanation": incident.explanation or "",
            "model_version": audit.model_version if audit else "n/a (score supplied in upload)",
            "top_model_factors": factors,
            "str_filed_at": incident.str_filed_at.isoformat() if incident.str_filed_at else "",
            "str_reference": incident.str_reference or "",
        }


@router.get("/audit-export")
def audit_export(
    request: Request,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    min_risk_score: float = Query(0.0, ge=0.0, le=1.0),
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(COMPLIANCE_AUDIT_EXPORT)),
):
    if end_date < start_date:
        raise HTTPException(400, "end_date must be on or after start_date")
    rows = list(_serialize_rows(db, user, start_date, end_date, min_risk_score))
    record_audit_event(
        db,
        user,
        "compliance.audit.export",
        "audit_export",
        "audit-export",
        request=request,
        metadata={
            "format": format,
            "min_risk_score": min_risk_score,
            "row_count": len(rows),
            "scope": "platform" if user.role == "owner" else "tenant",
        },
    )
    db.commit()
    if format == "json":
        return {
            "count": len(rows),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "rows": rows,
        }
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        buffer.write("no_rows_in_selected_window\n")
    filename = f"finsecai_audit_export_{start_date.date()}_{end_date.date()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class STRCandidate(BaseModel):
    incident_id: str
    user_id: str
    amount: float
    risk_score: float
    created_at: datetime
    hours_since_flagged: float
    sla_status: str
    str_filed_at: datetime | None = None


@router.get("/str-candidates", response_model=list[STRCandidate])
def str_candidates(
    db: Session = Depends(get_db), user: User = Depends(require_permission(COMPLIANCE_READ))
):
    now = datetime.now(timezone.utc)
    query = db.query(Incident).filter(
        Incident.risk_score >= settings.str_risk_threshold,
    )
    incidents = apply_tenant_scope(query, Incident, user).order_by(Incident.created_at.asc()).all()
    results = []
    for incident in incidents:
        created = incident.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        hours = (now - created).total_seconds() / 3600
        status = (
            "filed"
            if incident.str_filed_at
            else ("sla_breached" if hours > settings.str_reporting_sla_hours else "within_sla")
        )
        results.append(
            STRCandidate(
                incident_id=incident.id,
                user_id=incident.user_id,
                amount=incident.amount,
                risk_score=incident.risk_score,
                created_at=incident.created_at,
                hours_since_flagged=round(hours, 2),
                sla_status=status,
                str_filed_at=incident.str_filed_at,
            )
        )
    return results


class STRCreateRequest(BaseModel):
    incident_id: str
    narrative: str = Field(default="", max_length=20_000)


class STRUpdateRequest(BaseModel):
    narrative: str = Field(max_length=20_000)


class STRSubmitRequest(BaseModel):
    submission_reference: str | None = Field(default=None, max_length=256)


def _get_str_for_tenant(db: Session, str_id: str, user: User) -> SuspiciousTransactionReport:
    query = db.query(SuspiciousTransactionReport).filter(SuspiciousTransactionReport.id == str_id)
    report = apply_tenant_scope(query, SuspiciousTransactionReport, user).first()
    if not report:
        raise HTTPException(404, "STR not found")
    return report


@router.get("/str")
def list_strs(
    db: Session = Depends(get_db), user: User = Depends(require_permission(COMPLIANCE_READ))
):
    query = db.query(SuspiciousTransactionReport)
    return (
        apply_tenant_scope(query, SuspiciousTransactionReport, user)
        .order_by(SuspiciousTransactionReport.created_at.desc())
        .all()
    )


@router.post("/str", status_code=201)
def create_str(
    payload: STRCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(COMPLIANCE_STR_CREATE)),
):
    query = db.query(Incident).filter(Incident.id == payload.incident_id)
    incident = apply_tenant_scope(query, Incident, user).first()
    if not incident:
        raise HTTPException(404, "Incident not found")
    report = SuspiciousTransactionReport(
        tenant_id=incident.tenant_id,
        incident_id=incident.id,
        narrative=payload.narrative,
        created_by_user_id=user.id,
    )
    db.add(report)
    db.flush()
    record_audit_event(db, user, "compliance.str.create", "str", report.id, request=request)
    db.commit()
    db.refresh(report)
    return report


@router.patch("/str/{str_id}")
def update_str(
    str_id: str,
    payload: STRUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(COMPLIANCE_STR_UPDATE)),
):
    report = _get_str_for_tenant(db, str_id, user)
    if report.status == "submitted":
        raise HTTPException(409, "Submitted STRs cannot be edited")
    report.narrative = payload.narrative
    record_audit_event(db, user, "compliance.str.update", "str", report.id, request=request)
    db.commit()
    db.refresh(report)
    return report


@router.post("/str/{str_id}/submit")
def submit_str(
    str_id: str,
    payload: STRSubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(COMPLIANCE_STR_SUBMIT)),
):
    report = _get_str_for_tenant(db, str_id, user)
    if report.status == "submitted":
        raise HTTPException(409, "STR has already been submitted")
    report.status = "submitted"
    report.submitted_at = datetime.now(timezone.utc)
    report.submission_reference = payload.submission_reference
    query = db.query(Incident).filter(Incident.id == report.incident_id)
    incident = apply_tenant_scope(query, Incident, user).first()
    if incident:
        incident.str_filed_at = report.submitted_at
        incident.str_reference = payload.submission_reference
    record_audit_event(db, user, "compliance.str.submit", "str", report.id, request=request)
    db.commit()
    return {"status": "submitted", "submitted_at": report.submitted_at.isoformat()}


class MarkSTRFiledRequest(BaseModel):
    str_reference: str | None = Field(default=None, max_length=256)


@router.post("/{incident_id}/mark-str-filed")
def mark_str_filed(
    incident_id: str,
    payload: MarkSTRFiledRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(COMPLIANCE_STR_SUBMIT)),
):
    """Legacy equivalent of STR submission; maintained for existing integrations."""
    query = db.query(Incident).filter(Incident.id == incident_id)
    incident = apply_tenant_scope(query, Incident, user).first()
    if not incident:
        raise HTTPException(404, "Incident not found")
    incident.str_filed_at = datetime.now(timezone.utc)
    incident.str_reference = payload.str_reference
    record_audit_event(
        db,
        user,
        "compliance.str.submit",
        "incident",
        incident.id,
        request=request,
        metadata={"legacy_endpoint": True},
    )
    db.commit()
    return {"status": "recorded", "str_filed_at": incident.str_filed_at.isoformat()}
