"""Model version registry.

Every training run writes its artifacts into their own versioned directory
rather than overwriting a single fixed path -- this is what makes rollback
possible. A separate `active_version.json` pointer file says which version
is currently live; switching it is the entire rollback operation (no
retraining, no redeploying code, just repointing which artifacts get
loaded on next model access).

Layout:
    app/ml/artifacts/
        versions/
            bootstrap-v2-56f3bf751ff8/
                risk_classifier.joblib
                anomaly_detector.joblib
                model_metadata.json
            bootstrap-v2-<next-hash>/
                ...
        active_version.json   -> {"active_version": "bootstrap-v2-56f3bf751ff8"}

Nothing here deletes old versions automatically -- disk is cheap relative to
the cost of losing the ability to roll back or compare a regression against
what was live before it. Prune manually once you have a real retention
policy for model artifacts specifically (separate from the AML data
retention policy in app.core.retention, which governs prediction *records*,
not model *artifacts*).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("finsecai.ml.registry")

ARTIFACT_ROOT = Path(__file__).parent / "artifacts"
VERSIONS_DIR = ARTIFACT_ROOT / "versions"
ACTIVE_POINTER_PATH = ARTIFACT_ROOT / "active_version.json"

ALLOWED_LIFECYCLE_STATES = {
    "EXPERIMENTAL",
    "EVALUATED",
    "VALIDATION_FAILED",
    "CANDIDATE",
    "APPROVED",
    "ACTIVE",
    "RETIRED",
}

ELIGIBLE_PROMOTION_STATES = {"CANDIDATE", "APPROVED"}


class UnknownModelVersion(Exception):
    pass


def _metadata_for_version(version: str) -> dict:
    metadata_path = get_version_dir(version) / "model_metadata.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8-sig"))


def _normalize_status(metadata: dict) -> str | None:
    status = metadata.get("lifecycle_status") or metadata.get("status")
    if status is None:
        return None
    return str(status).upper()


def get_version_dir(version: str) -> Path:
    return VERSIONS_DIR / version


def list_versions() -> list[dict]:
    """All registered versions with their metadata, newest first by
    directory mtime. Includes whether each is currently active."""
    if not VERSIONS_DIR.exists():
        return []
    active = get_active_version()
    versions = []
    for version_dir in sorted(VERSIONS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not version_dir.is_dir():
            continue
        metadata_path = version_dir / "model_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig")) if metadata_path.exists() else {}
        versions.append({
            "version": version_dir.name,
            "is_active": version_dir.name == active,
            "trained_at": metadata.get("trained_at"),
            "training_data_source": metadata.get("training_data_source"),
            "eval_metrics": metadata.get("eval_metrics"),
        })
    return versions


def get_active_version() -> str | None:
    if not ACTIVE_POINTER_PATH.exists():
        return None
    try:
        return json.loads(ACTIVE_POINTER_PATH.read_text(encoding="utf-8-sig")).get("active_version")
    except (json.JSONDecodeError, OSError):
        return None


def _write_governance_manifest(version: str | None, status: str) -> None:
    manifest_path = Path(__file__).resolve().parents[2] / "artifacts" / "production" / "production_model.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "active_version": version,
        "status": status,
        "runtime_pointer": str(ACTIVE_POINTER_PATH),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def set_active_version(version: str) -> None:
    """The entire rollback operation. Validates the version exists before
    switching, and writes atomically (write to a temp file, then rename) so
    a crash mid-write can't leave the pointer file half-written and every
    subsequent model load broken."""
    version_dir = get_version_dir(version)
    if not version_dir.exists():
        available = [v["version"] for v in list_versions()]
        raise UnknownModelVersion(f"No such model version: {version!r}. Available: {available}")

    tmp_path = ACTIVE_POINTER_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps({"active_version": version}), encoding="utf-8")
    tmp_path.replace(ACTIVE_POINTER_PATH)
    _write_governance_manifest(version, "ACTIVE")
    logger.info("Active model version set to %s", version)


def register_version(version: str) -> Path:
    """Called by train.py after writing artifacts into a version directory.
    Returns the directory path for train.py to write artifacts into."""
    version_dir = get_version_dir(version)
    version_dir.mkdir(parents=True, exist_ok=True)
    return version_dir


def promote_to_production(version: str, promoted_by: str, reason: str | None = None) -> dict:
    """Promote an already-registered model version to production.

    Promotion is now lifecycle-gated. A version must already be in a
    governance-eligible state (CANDIDATE or APPROVED) and must not have been
    marked VALIDATION_FAILED. The function remains non-destructive: it never
    deletes old versions and leaves rollback available through the active pointer.
    """
    version_dir = get_version_dir(version)
    if not version_dir.exists():
        available = [v["version"] for v in list_versions()]
        raise UnknownModelVersion(f"No such model version: {version!r}. Available: {available}")

    metadata_path = version_dir / "model_metadata.json"
    metadata = _metadata_for_version(version)
    lifecycle_status = _normalize_status(metadata)
    if lifecycle_status == "VALIDATION_FAILED":
        raise ValueError(
            f"Model {version!r} is marked VALIDATION_FAILED and cannot be promoted."
        )
    if lifecycle_status not in ELIGIBLE_PROMOTION_STATES:
        raise ValueError(
            f"Model {version!r} has lifecycle status {lifecycle_status!r}; only CANDIDATE or APPROVED models may be promoted."
        )

    metadata.update(
        {
            "promoted_to_production": True,
            "production_promoted_by": promoted_by,
            "production_promoted_at": datetime.now(timezone.utc).isoformat(),
            "production_promotion_reason": reason or "",
            "lifecycle_status": "ACTIVE",
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    set_active_version(version)
    _write_governance_manifest(version, "ACTIVE")

    return {
        "active_version": version,
        "promoted_by": promoted_by,
        "reason": reason,
        "metadata_path": str(metadata_path),
        "lifecycle_status": "ACTIVE",
    }
