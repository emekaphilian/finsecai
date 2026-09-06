"""Feature-distribution drift detection.

The model was trained on a fixed reference distribution (synthetic today,
real transactions eventually). Production traffic can drift away from that
distribution over time -- new fraud typologies, seasonal transaction
patterns, a business launching a new product with different amount ranges.
When that happens, the model's learned decision boundary no longer matches
reality, and accuracy silently degrades without anything necessarily
crashing or erroring.

APPROACH: Population Stability Index (PSI) per feature, comparing a
rolling window of recent production feature values (pulled from
MLPredictionAudit.feature_values, which is already recorded for every
model prediction) against the reference distribution recorded at training
time.

PSI interpretation (standard industry thresholds):
    < 0.1  -- no significant shift
    0.1-0.25 -- moderate shift, worth watching
    > 0.25 -- significant shift, the model may need retraining

This is a periodic check (run via CLI or a scheduled job), not a per-request
computation -- drift is a trend over hundreds/thousands of predictions, not
something meaningful to compute per single prediction.
"""

from __future__ import annotations

import logging

import numpy as np
from sqlalchemy.orm import Session

from app.db.models import MLPredictionAudit
from app.ml.features import FEATURE_NAMES

logger = logging.getLogger("finsecai.ml.drift")

_PSI_BUCKETS = 10


def _psi_for_feature(reference: np.ndarray, current: np.ndarray) -> float:
    """PSI between two 1D arrays of a single feature's values, using
    reference-derived quantile bucket edges (standard PSI methodology --
    the buckets are defined by the reference/expected distribution, then
    both distributions are binned into those same edges)."""
    if len(reference) < 10 or len(current) < 10:
        return 0.0  # not enough data in either window to say anything meaningful

    quantiles = np.linspace(0, 100, _PSI_BUCKETS + 1)
    edges = np.unique(np.percentile(reference, quantiles))
    if len(edges) < 3:
        return 0.0  # reference feature has near-zero variance (e.g. a constant flag); PSI undefined/meaningless here

    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)

    ref_pct = np.clip(ref_counts / max(1, ref_counts.sum()), 1e-4, None)
    cur_pct = np.clip(cur_counts / max(1, cur_counts.sum()), 1e-4, None)

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def compute_feature_drift(
    db: Session,
    tenant_id: str,
    reference_values: dict[str, list[float]],
    window_size: int = 500,
) -> dict[str, dict]:
    """reference_values: {feature_name: [values from training data]} --
    train.py should export this (see model_metadata's "reference_distribution"
    key, added alongside eval_metrics) so drift is checked against what the
    live model actually learned from, not an arbitrary separate sample.

    Returns {feature_name: {"psi": float, "status": str, "n_samples": int}}.
    """
    recent = (
        db.query(MLPredictionAudit.feature_values)
        .filter(MLPredictionAudit.tenant_id == tenant_id)
        .order_by(MLPredictionAudit.created_at.desc())
        .limit(window_size)
        .all()
    )
    if len(recent) < 30:
        logger.info("Only %d recent predictions for tenant %s; too few to assess drift meaningfully (need 30+).", len(recent), tenant_id)
        return {}

    current_by_feature: dict[str, list[float]] = {name: [] for name in FEATURE_NAMES}
    for (values,) in recent:
        for name in FEATURE_NAMES:
            if name in values:
                current_by_feature[name].append(values[name])

    results = {}
    for name in FEATURE_NAMES:
        ref = np.array(reference_values.get(name, []))
        cur = np.array(current_by_feature.get(name, []))
        if len(ref) == 0 or len(cur) == 0:
            continue
        psi = _psi_for_feature(ref, cur)
        if psi < 0.1:
            status = "stable"
        elif psi < 0.25:
            status = "moderate_shift"
        else:
            status = "significant_shift"
        results[name] = {"psi": round(psi, 4), "status": status, "n_samples": len(cur)}

    return results
