"""Offline training for the fraud risk classifier + anomaly detector.

Run manually (not part of the API request path):

    python -m app.ml.train

Produces three artifacts in app/ml/artifacts/:
    risk_classifier.joblib   - XGBoost binary classifier (fraud probability)
    anomaly_detector.joblib  - IsolationForest (unsupervised outlier score)
    model_metadata.json      - version hash, training timestamp, eval metrics,
                               feature names (for drift/mismatch detection)

TRAINING DATA
-------------
Currently trains on bootstrap_data.generate_bootstrap_dataset(), a synthetic
dataset -- see that module's docstring for why. When real labels exist in
the `feedback` table (Feedback.label: true_positive/false_positive, joined
back to the Incident it's attached to), retrain against that instead:
swap load_training_data() below to query the DB, join Feedback -> Incident,
and reconstruct the same feature columns via a query using
app.ml.features.TransactionHistory (built incrementally, ordered by
created_at, so velocity/zscore/reuse features are computed the same way at
train time as at inference time -- this ordering detail matters, a naive
full-history feature build would leak future information into past rows).
Everything downstream (training loop, artifact format, metadata) stays the
same -- only the data source changes.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

logger = logging.getLogger("finsecai.ml.train")


from app.ml.bootstrap_data import generate_bootstrap_dataset
from app.ml.features import FEATURE_NAMES, build_features_from_values
from app.ml.model_registry import register_version, set_active_version

ARTIFACT_DIR = Path(__file__).parent / "artifacts"


def load_training_data() -> tuple[np.ndarray, np.ndarray]:
    """Returns (X, y). Swap this function's body to pull from the Feedback
    table once real labels exist -- see module docstring."""
    df = generate_bootstrap_dataset(n=20000)
    X = np.array(
        [
            build_features_from_values(
                amount=row.amount,
                transaction_type=row.transaction_type,
                device_reuse_count=row.device_reuse_count,
                is_device_missing=bool(row.is_device_missing),
                velocity_1h=row.velocity_1h,
                user_amount_zscore=row.user_amount_zscore,
                is_new_device_for_user=bool(row.is_new_device_for_user),
            )
            for row in df.itertuples()
        ]
    )
    y = df["is_fraud"].to_numpy()
    return X, y


def _sample_reference_distribution(X_train: np.ndarray, max_samples: int = 2000) -> dict[str, list[float]]:
    rng = np.random.default_rng(42)
    n = len(X_train)
    idx = rng.choice(n, size=min(max_samples, n), replace=False)
    sample = X_train[idx]
    return {name: sample[:, i].round(4).tolist() for i, name in enumerate(FEATURE_NAMES)}


def _threshold_analysis(y_true: np.ndarray, y_score: np.ndarray) -> list[dict]:
    rows: list[dict] = []
    for threshold in np.linspace(0.1, 0.95, 18):
        preds = (y_score >= threshold).astype(int)
        precision, recall, _, _ = precision_recall_fscore_support(
            y_true, preds, average="binary", zero_division=0
        )
        alerts = int(preds.sum())
        rows.append(
            {
                "threshold": round(float(threshold), 2),
                "precision": round(float(precision), 4),
                "recall": round(float(recall), 4),
                "alerts": alerts,
                "alert_rate": round(float(alerts / len(y_true)), 6),
            }
        )
    return rows


def _precision_recall_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int | None = None) -> tuple[float, float]:
    if len(y_true) == 0:
        return 0.0, 0.0
    if k is None:
        k = max(1, min(len(y_true), int(round(len(y_true) * 0.05))))
    else:
        k = max(1, min(len(y_true), int(k)))
    order = np.argsort(y_score)[::-1]
    top_k = y_true[order[:k]]
    precision_at_k = float(top_k.mean()) if len(top_k) else 0.0
    actual_positives = int(y_true.sum())
    recall_at_k = float(top_k.sum() / max(1, actual_positives)) if actual_positives else 0.0
    return precision_at_k, recall_at_k


def train(activate: bool = False) -> dict:
    X, y = load_training_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    classifier = XGBClassifier(
        n_estimators=250,
        max_depth=5,
        learning_rate=0.07,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="aucpr",
        scale_pos_weight=(y_train == 0).sum() / max(1, (y_train == 1).sum()),
        random_state=42,
    )
    classifier.fit(X_train, y_train)

    y_pred_proba = classifier.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    auc = roc_auc_score(y_test, y_pred_proba)
    pr_auc = average_precision_score(y_test, y_pred_proba)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="binary", zero_division=0
    )
    # precision@k / recall@k for 1%,2%,5%,10% operational points
    def compute_k_metrics(pct):
        k = max(1, int(len(y_test) * pct))
        pk, rk = _precision_recall_at_k(y_test, y_pred_proba, k=k)
        return pk, rk, k
    pk1, rk1, k1 = compute_k_metrics(0.01)
    pk2, rk2, k2 = compute_k_metrics(0.02)
    pk5, rk5, k5 = compute_k_metrics(0.05)
    pk10, rk10, k10 = compute_k_metrics(0.10)
    precision_at_k, recall_at_k = pk5, rk5 # default 5% for backward compat

    threshold_analysis = _threshold_analysis(y_test, y_pred_proba)
    alerts_at_default_threshold = int((y_pred_proba >= 0.5).sum())
    alert_rate_at_default = round(float(alerts_at_default_threshold / len(y_test)), 6)
    calibration = {
        "brier_score": round(float(brier_score_loss(y_test, y_pred_proba)), 4),
    }

    anomaly_detector = IsolationForest(
        n_estimators=200, contamination=0.08, random_state=42
    )
    anomaly_detector.fit(X)

    params_hash = hashlib.sha256(
        json.dumps(classifier.get_params(), sort_keys=True).encode()
    ).hexdigest()[:12]
    run_signature = hashlib.sha256(
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{len(X_train)}-{len(y_train)}-{params_hash}".encode()
    ).hexdigest()[:16]
    model_version = f"bootstrap-v3-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{run_signature[:12]}"

    # Versioned artifact directory -- see model_registry.py. Writing here
    # instead of a fixed path is what makes rollback possible: this training
    # run's artifacts never overwrite a previous version's.
    version_dir = register_version(model_version)
    joblib.dump(classifier, version_dir / "risk_classifier.joblib")
    joblib.dump(anomaly_detector, version_dir / "anomaly_detector.joblib")

    classifier_hash = hashlib.sha256((version_dir / "risk_classifier.joblib").read_bytes()).hexdigest()
    anomaly_hash = hashlib.sha256((version_dir / "anomaly_detector.joblib").read_bytes()).hexdigest()

    metadata = {
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_data_source": "synthetic_bootstrap_v2",
        "feature_names": FEATURE_NAMES,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "artifact_checksums": {
            "risk_classifier.joblib": classifier_hash,
            "anomaly_detector.joblib": anomaly_hash,
        },
        "eval_metrics": {
            "roc_auc": round(float(auc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "average_precision": round(float(pr_auc), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "precision_at_k": round(float(precision_at_k), 4),
            "recall_at_k": round(float(recall_at_k), 4),
            "precision_at_1pct": round(float(pk1), 4),
            "recall_at_1pct": round(float(rk1), 4),
            "precision_at_2pct": round(float(pk2), 4),
            "recall_at_2pct": round(float(rk2), 4),
            "precision_at_5pct": round(float(pk5), 4),
            "recall_at_5pct": round(float(rk5), 4),
            "precision_at_10pct": round(float(pk10), 4),
            "recall_at_10pct": round(float(rk10), 4),
            "alert_volume": alerts_at_default_threshold,
            "alert_rate": alert_rate_at_default,
            "calibration": calibration,
            "threshold_analysis": threshold_analysis,
        },
        # Reference distribution for drift detection (see app.ml.drift). A
        # random subsample of the training features, not the full training
        # set -- enough to estimate quantile buckets accurately without
        # bloating model_metadata.json. Stored per-feature-name so drift.py
        # can compare production traffic against exactly what this model
        # version was actually trained on.
        "reference_distribution": _sample_reference_distribution(X_train),
        "lifecycle_status": "CANDIDATE",
        "non_active_by_default": True,
    }
    (version_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2))

    if activate:
        set_active_version(model_version)
    else:
        logger.info("Trained %s but did not activate it (activate=False). "
                     "It won't be served until explicitly activated.", model_version)

    return metadata


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--activate", action="store_true", help="Activate the newly registered model after training.")
    parser.add_argument("--no-activate", action="store_true", help="Keep the model non-active (default behavior).")
    args = parser.parse_args()
    metadata = train(activate=args.activate)
    print(json.dumps(metadata, indent=2))
