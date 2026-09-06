"""Fraud risk classifier: inference + SHAP explainability wrapper.

Loaded once at process startup (see get_risk_model()), reused across
requests. Two models are bundled together because they answer different
questions:

  - risk_score:    supervised XGBoost probability of fraud (0-1). This is
                    the number that drives governance_flags_for's
                    HIGH_RISK_REVIEW_REQUIRED threshold, so it must be a
                    calibrated probability, not a raw score.
  - anomaly_score:  unsupervised IsolationForest outlier score (0-1,
                    normalized). Catches transactions that look unusual even
                    if they don't match known fraud patterns the supervised
                    model was trained on -- useful because the bootstrap
                    training set (see bootstrap_data.py) can't cover every
                    real-world typology.

SHAP (TreeExplainer) is only computed for the supervised model -- it's cheap
for tree ensembles (milliseconds) and its output has a clear "this feature
pushed the score up/down by X" meaning, which is what the CBN audit trail
and the LLM's explanation prompt both need. The IsolationForest score is
reported but not SHAP-explained; per-tree isolation depth isn't as
interpretable, and the audit record already has the supervised model's
attributions as the primary "why" signal.
"""

from __future__ import annotations

import json
import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

try:
    import shap
except (ImportError, OSError):
    shap = None

from app.core.metrics import record_prediction, set_active_model_version_metric
from app.ml.features import FEATURE_NAMES
from app.ml.model_registry import ARTIFACT_ROOT, get_active_version, get_version_dir

logger = logging.getLogger("finsecai.ml")

ARTIFACT_DIR = ARTIFACT_ROOT  # kept for anything importing the old name


@dataclass
class Prediction:
    risk_score: float
    anomaly_score: float
    confidence: float
    model_version: str
    feature_contributions: list[dict]  # [{"feature": str, "value": float, "shap": float}, ...]


class RiskModel:
    def __init__(self, version: str | None = None):
        """Loads the given model version, or the currently active one if
        version is None (the normal case -- get_risk_model() always passes
        None, so process startup always loads whatever's currently active).
        Explicit version loading exists for tooling (e.g. comparing two
        versions' predictions side by side) rather than for the request path.
        """
        resolved_version = version or get_active_version()
        if resolved_version is None:
            raise FileNotFoundError(
                "No active model version set. Run `python -m app.ml.train` first."
            )
        version_dir = get_version_dir(resolved_version)
        model_path = version_dir / "risk_classifier.joblib"
        anomaly_path = version_dir / "anomaly_detector.joblib"
        metadata_path = version_dir / "model_metadata.json"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model version {resolved_version!r} is registered as active but its "
                f"artifact file is missing at {model_path}. Retrain or roll back to a "
                f"different version with app.ml.model_registry.set_active_version()."
            )
        self.metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        self._verify_artifact_integrity(model_path, anomaly_path)

        self.classifier = joblib.load(model_path)
        self.anomaly_detector = joblib.load(anomaly_path)
        self.model_version = self.metadata.get("model_version", resolved_version)
        self._explainer = shap.TreeExplainer(self.classifier) if shap is not None else None
        if self._explainer is None:
            logger.warning("SHAP unavailable; risk predictions will omit feature attributions")
        set_active_model_version_metric(self.model_version)

    def _verify_artifact_integrity(self, model_path: Path, anomaly_path: Path) -> None:
        """Checks each artifact's SHA256 against the checksum train.py
        recorded in model_metadata.json. Raises if they don't match -- a
        mismatch means the file on disk isn't what was actually trained
        (corrupted, truncated, or replaced), and joblib.load() should not
        proceed to deserialize it. Older metadata files without checksums
        (pre-Tier-3 artifacts) log a warning and proceed rather than hard
        failing, so this doesn't break existing deployments on upgrade --
        retrain once to get checksums recorded going forward."""
        checksums = self.metadata.get("artifact_checksums")
        if not checksums:
            logger.warning(
                "model_metadata.json has no artifact_checksums (older artifact set?); "
                "skipping integrity check. Retrain with `python -m app.ml.train` to enable it."
            )
            return

        for path, filename in [(model_path, "risk_classifier.joblib"), (anomaly_path, "anomaly_detector.joblib")]:
            expected = checksums.get(filename)
            if not expected:
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(
                    f"Integrity check failed for {filename}: checksum on disk does not match "
                    f"model_metadata.json. The file may be corrupted or was replaced after "
                    f"training. Refusing to load. Retrain with `python -m app.ml.train`."
                )

    def predict(self, feature_vector: list[float]) -> Prediction:
        start = time.perf_counter()
        x = np.array([feature_vector], dtype=float)

        risk_score = float(self.classifier.predict_proba(x)[0, 1])

        # IsolationForest: decision_function is higher = more normal, lower = more anomalous.
        # Normalize to 0-1 where 1 = most anomalous, via the raw score's sigmoid.
        raw_anomaly = float(self.anomaly_detector.decision_function(x)[0])
        anomaly_score = float(1 / (1 + np.exp(raw_anomaly * 5)))  # steeper sigmoid, centered at 0

        confidence = float(max(risk_score, 1 - risk_score))

        if self._explainer is None:
            row = [0.0] * len(feature_vector)
        else:
            shap_values = self._explainer.shap_values(x)
            # TreeExplainer on a binary XGBClassifier returns either a single array
            # (positive class) or a list [neg, pos] depending on version; handle both.
            row = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]

        contributions = [
            {"feature": name, "value": float(val), "shap": float(shap_val)}
            for name, val, shap_val in zip(FEATURE_NAMES, feature_vector, row)
        ]
        contributions.sort(key=lambda c: abs(c["shap"]), reverse=True)

        record_prediction(self.model_version, risk_score, time.perf_counter() - start)

        return Prediction(
            risk_score=risk_score,
            anomaly_score=anomaly_score,
            confidence=confidence,
            model_version=self.model_version,
            feature_contributions=contributions,
        )


_lock = threading.Lock()
_instance: RiskModel | None = None


def get_risk_model() -> RiskModel:
    """Singleton accessor. Raises FileNotFoundError with a clear message if
    train.py hasn't been run yet -- callers (upload_incidents) should catch
    this and fall back to requiring risk_score/anomaly_score in the upload,
    same as current behavior, rather than hard-failing the endpoint."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = RiskModel()
    return _instance


def reload_risk_model() -> RiskModel:
    """Forces the singleton to re-resolve the active version and reload.
    Call this after app.ml.model_registry.set_active_version() (e.g. from
    a rollback endpoint/CLI) if you want the change to take effect in a
    running process immediately, rather than waiting for the next restart.
    Without calling this, a rollback updates the pointer file correctly but
    a long-running process keeps serving whatever it already loaded."""
    global _instance
    with _lock:
        _instance = RiskModel()
    return _instance
