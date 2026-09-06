"""Owner-only ML operations with model version management and audit logging."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.authorization import MODELS_MANAGE, apply_enterprise_scope, require_permission
from app.db.models import Incident, User
from app.db.session import get_db
from app.ml import model_registry
from app.ml.risk_model import get_risk_model, reload_risk_model
from app.services import evaluation_service
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/versions")
def list_model_versions(user: User = Depends(require_permission(MODELS_MANAGE))):
    return {"versions": model_registry.list_versions()}


@router.post("/rollback")
def rollback_model_version(
    version: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(MODELS_MANAGE)),
):
    previous_version = model_registry.get_active_version()
    try:
        model_registry.set_active_version(version)
    except model_registry.UnknownModelVersion as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    reload_risk_model()
    record_audit_event(
        db,
        user,
        "ml.rollback",
        "model_version",
        version,
        request=request,
        metadata={
            "previous_active_version": previous_version,
            "new_active_version": version,
        },
    )
    db.commit()
    return {"active_model_version": version, "previous_version": previous_version}


@router.get("/drift")
def platform_drift(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(MODELS_MANAGE)),
):
    incidents = apply_enterprise_scope(
        db.query(Incident).order_by(Incident.created_at), Incident
    ).all()
    risk_scores = [incident.risk_score for incident in incidents]
    mid = len(risk_scores) // 2
    # PSI is defined here over the predicted-positive rate, not raw continuous
    # probabilities. Binarize with the same threshold helper used by analytics.
    baseline_labels = evaluation_service.predict_labels(risk_scores[:mid])
    current_labels = evaluation_service.predict_labels(risk_scores[mid:])
    drift_metrics = evaluation_service.compute_drift(baseline_labels, current_labels)

    record_audit_event(
        db,
        user,
        "ml.drift",
        "model_drift",
        model_registry.get_active_version() or get_risk_model().model_version,
        request=request,
        metadata={
            "incident_count": len(incidents),
            "active_model_version": model_registry.get_active_version(),
        },
    )
    db.commit()
    return {
        "active_model_version": model_registry.get_active_version(),
        "drift": drift_metrics,
    }
