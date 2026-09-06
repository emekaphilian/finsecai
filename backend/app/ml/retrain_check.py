"""Retraining cadence check.

Not a scheduler itself -- this script makes ONE decision (retrain now or
not) based on two independent triggers, and exits. Wire it to an actual
scheduler for your deployment platform:

    # cron (daily at 3am)
    0 3 * * * cd /path/to/backend && python -m app.ml.retrain_check >> /var/log/finsecai/retrain.log 2>&1

    # systemd timer -- create finsecai-retrain.service + .timer instead of cron
    # if the deployment platform uses systemd

    # Cloud Scheduler / EventBridge / etc. -- if the eventual deployment
    # platform (still undecided, and now gated by CBN's data-localization
    # requirement -- see Tier 5 notes) has a managed scheduler, prefer it
    # over cron for observability/retry semantics.

TRIGGER 1 -- enough new labeled feedback exists. Checks the Feedback table
for rows created since the currently-active model's trained_at timestamp.
Retraining on too few new labels just adds noise; the threshold below
(--min-new-feedback) is a starting guess, not a validated number -- revisit
once you have a sense of how much feedback volume actually moves model
quality in practice.

TRIGGER 2 -- drift detected. If app.ml.drift flags any feature as
significant_shift for any tenant, that alone is a reason to retrain
regardless of feedback volume, since it means the live model no longer
matches production reality.

This intentionally does NOT auto-activate a retrained model without a human
decision point when triggered by feedback volume -- see --auto-activate.
Drift-triggered retrains also default to NOT auto-activating: a drift-
triggered retrain deserves a look at the new eval metrics before going live,
not a silent swap.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from app.db.models import Feedback, Tenant
from app.db.session import SessionLocal
from app.ml.drift import compute_feature_drift
from app.ml.model_registry import get_active_version, list_versions
from app.ml.risk_model import get_risk_model
from app.ml.train import train

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("finsecai.ml.retrain_check")


def _active_model_trained_at() -> str | None:
    for v in list_versions():
        if v["is_active"]:
            return v["trained_at"]
    return None


def _new_feedback_count(db, since: str | None) -> int:
    q = db.query(Feedback)
    if since:
        # `since` comes from model_metadata.json as an ISO string
        # (datetime.now(timezone.utc).isoformat()). It must be parsed into
        # an actual datetime before filtering -- comparing a DateTime column
        # against a raw string works differently across DB backends (and on
        # SQLite, silently does a lexicographic string comparison that
        # doesn't match Feedback.created_at's stored format, undercounting
        # silently rather than erroring). Caught this via testing, not
        # inspection -- worth remembering as a general lesson for any other
        # str-vs-DateTime filter in this codebase.
        since_dt = datetime.fromisoformat(since)
        if since_dt.tzinfo is not None:
            # Feedback.created_at uses default=datetime.utcnow (naive UTC).
            # since_dt parsed from metadata is timezone-aware. Normalize to
            # naive UTC before comparing, or the two datetimes silently
            # fail to compare correctly rather than raising -- same class
            # of bug as above, worth being explicit about.
            since_dt = since_dt.astimezone(timezone.utc).replace(tzinfo=None)
        q = q.filter(Feedback.created_at >= since_dt)
    return q.count()


def _any_tenant_drifted(db) -> bool:
    try:
        model = get_risk_model()
    except FileNotFoundError:
        return False
    reference = model.metadata.get("reference_distribution")
    if not reference:
        return False

    for (tenant_id,) in db.query(Tenant.id).all():
        results = compute_feature_drift(db, tenant_id, reference)
        if any(r["status"] == "significant_shift" for r in results.values()):
            logger.info("Drift detected for tenant %s", tenant_id)
            return True
    return False


def check_and_maybe_retrain(min_new_feedback: int = 200, auto_activate: bool = False) -> dict:
    db = SessionLocal()
    try:
        since = _active_model_trained_at()
        feedback_count = _new_feedback_count(db, since)
        drifted = _any_tenant_drifted(db)

        should_retrain = feedback_count >= min_new_feedback or drifted
        result = {
            "active_version": get_active_version(),
            "new_feedback_since_last_train": feedback_count,
            "min_new_feedback_threshold": min_new_feedback,
            "drift_detected": drifted,
            "retrained": False,
        }

        if not should_retrain:
            logger.info("No retrain trigger met (feedback=%d/%d, drift=%s). Skipping.", feedback_count, min_new_feedback, drifted)
            return result

        reason = "drift" if drifted else "feedback_volume"
        logger.info("Retrain triggered (reason=%s). Training new version...", reason)
        metadata = train(activate=auto_activate)
        result["retrained"] = True
        result["new_version"] = metadata["model_version"]
        result["activated"] = auto_activate
        result["trigger_reason"] = reason
        if not auto_activate:
            logger.warning(
                "New version %s trained but NOT activated (auto_activate=False). "
                "Review eval_metrics and activate manually via POST /ml/rollback "
                "or app.ml.model_registry.set_active_version() once satisfied.",
                metadata["model_version"],
            )
        return result
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-new-feedback", type=int, default=200)
    parser.add_argument("--auto-activate", action="store_true", help="Activate the retrained model immediately instead of leaving it for manual review.")
    args = parser.parse_args()
    result = check_and_maybe_retrain(min_new_feedback=args.min_new_feedback, auto_activate=args.auto_activate)
    print(result)
