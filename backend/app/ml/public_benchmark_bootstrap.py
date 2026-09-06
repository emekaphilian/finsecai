"""Download public fraud benchmarks and train an evaluation-only FinSecAI model.

This command intentionally does *not* activate its output by default. Public
benchmarks have different populations and field semantics from a customer's
production traffic, so the resulting model is useful for pipeline evaluation,
not production decisioning.

Run from ``backend/`` after configuring Kaggle credentials::

    python -m app.ml.public_benchmark_bootstrap

The IEEE-CIS competition additionally requires accepting its rules in Kaggle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, precision_recall_fscore_support, roc_auc_score
from xgboost import XGBClassifier

from app.ml.features import FEATURE_NAMES, build_features_from_values
from app.ml.model_registry import register_version, set_active_version

DATA_ROOT = Path("datasets/public_benchmark")
RNG_SEED = 42


def _download_kaggle_sources() -> dict[str, Path]:
    """Download once and copy the required CSVs into a stable project location."""
    try:
        import kagglehub
    except ImportError as exc:
        raise RuntimeError("kagglehub is required; install backend/requirements.txt first.") from exc

    paths = {
        "ieee": DATA_ROOT / "ieee_fraud",
        "paysim": DATA_ROOT / "paysim",
        "creditcard": DATA_ROOT / "creditcard",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    ieee_required = [paths["ieee"] / "train_transaction.csv", paths["ieee"] / "train_identity.csv"]
    if not all(path.exists() for path in ieee_required):
        downloaded = Path(kagglehub.competition_download("ieee-fraud-detection"))
        for name in ("train_transaction.csv", "train_identity.csv"):
            source = next(downloaded.rglob(name), None)
            if source is None:
                raise FileNotFoundError(f"IEEE download did not contain {name}")
            shutil.copy2(source, paths["ieee"] / name)

    paysim_target = paths["paysim"] / "PS_20174392719_1491204439457_log.csv"
    if not paysim_target.exists():
        downloaded = Path(kagglehub.dataset_download("ealaxi/paysim1"))
        source = next(downloaded.rglob("*.csv"), None)
        if source is None:
            raise FileNotFoundError("PaySim download did not contain a CSV")
        shutil.copy2(source, paysim_target)

    credit_target = paths["creditcard"] / "creditcard.csv"
    if not credit_target.exists():
        downloaded = Path(kagglehub.dataset_download("mlg-ulb/creditcardfraud"))
        source = next(downloaded.rglob("creditcard.csv"), None)
        if source is None:
            raise FileNotFoundError("Credit-card download did not contain creditcard.csv")
        shutil.copy2(source, credit_target)
    return paths


def _sample(frame: pd.DataFrame, limit: int, label: str) -> pd.DataFrame:
    if len(frame) <= limit:
        return frame
    # Preserve rare positives while sampling, deterministically.
    positives = frame[frame.is_fraud == 1]
    negatives = frame[frame.is_fraud == 0]
    keep_positive = positives.sample(min(len(positives), max(1, limit // 2)), random_state=RNG_SEED)
    keep_negative = negatives.sample(limit - len(keep_positive), random_state=RNG_SEED)
    result = pd.concat([keep_positive, keep_negative], ignore_index=True)
    print(f"{label}: sampled {len(frame):,} -> {len(result):,} rows")
    return result


def _load_ieee(path: Path, limit: int) -> pd.DataFrame:
    transaction = pd.read_csv(
        path / "train_transaction.csv",
        usecols=["TransactionID", "TransactionDT", "isFraud", "TransactionAmt", "ProductCD", "card1"],
    )
    identity = pd.read_csv(path / "train_identity.csv", usecols=["TransactionID", "DeviceInfo"])
    frame = transaction.merge(identity, on="TransactionID", how="left")
    result = pd.DataFrame({
        "source": "ieee_cis",
        "user_id": "ieee_card_" + frame.card1.fillna(-1).astype(str),
        "amount": frame.TransactionAmt,
        "transaction_type": frame.ProductCD.map({"W": "PAYMENT", "C": "TRANSFER", "R": "TRANSFER", "S": "PAYMENT", "H": "PAYMENT"}).fillna("PAYMENT"),
        "device_id": frame.DeviceInfo.fillna("").astype(str),
        "event_time": frame.TransactionDT.astype(float),
        "is_fraud": frame.isFraud.astype(int),
    })
    return _sample(result, limit, "IEEE-CIS")


def _load_paysim(path: Path, limit: int) -> pd.DataFrame:
    frame = pd.read_csv(path / "PS_20174392719_1491204439457_log.csv")
    tx_types = {"TRANSFER": "TRANSFER", "CASH_OUT": "WITHDRAWAL", "CASH_IN": "DEPOSIT", "PAYMENT": "PAYMENT", "DEBIT": "PAYMENT"}
    result = pd.DataFrame({
        "source": "paysim",
        "user_id": frame.nameOrig.astype(str),
        "amount": frame.amount,
        "transaction_type": frame.type.map(tx_types).fillna("PAYMENT"),
        # PaySim has no device identifier. Destination is retained only as a proxy feature.
        "device_id": "paysim_dest_" + frame.nameDest.astype(str),
        "event_time": frame.step.astype(float) * 3600,
        "is_fraud": frame.isFraud.astype(int),
    })
    return _sample(result, limit, "PaySim")


def _load_creditcard(path: Path, limit: int) -> pd.DataFrame:
    frame = pd.read_csv(path / "creditcard.csv", usecols=["Time", "Amount", "Class"])
    # This data has no account, device, or payment-type identifiers; deterministic
    # pseudonyms make the missing context explicit rather than inventing it.
    result = pd.DataFrame({
        "source": "creditcard",
        "user_id": "creditcard_unknown",
        "amount": frame.Amount,
        "transaction_type": "PAYMENT",
        "device_id": "",
        "event_time": frame.Time.astype(float),
        "is_fraud": frame.Class.astype(int),
    })
    return _sample(result, limit, "Credit Card")


def _features_for_source(frame: pd.DataFrame) -> pd.DataFrame:
    """Generate the same online-style features in time order, without labels."""
    frame = frame.sort_values("event_time", kind="stable").reset_index(drop=True).copy()
    users_by_device: dict[str, set[str]] = defaultdict(set)
    devices_by_user: dict[str, set[str]] = defaultdict(set)
    amounts_by_user: dict[str, list[float]] = defaultdict(list)
    recent_by_user: dict[str, list[float]] = defaultdict(list)
    vectors: list[list[float]] = []
    for row in frame.itertuples(index=False):
        device = str(row.device_id)
        user = str(row.user_id)
        amount = float(row.amount)
        timestamp = float(row.event_time)
        recent = [time for time in recent_by_user[user] if time >= timestamp - 3600]
        recent_by_user[user] = recent
        prior_amounts = amounts_by_user[user]
        if len(prior_amounts) >= 2:
            mean = float(np.mean(prior_amounts))
            std = float(np.std(prior_amounts))
            zscore = (amount - mean) / std if std > 0 else 0.0
        else:
            zscore = 0.0
        vectors.append(build_features_from_values(
            amount, row.transaction_type,
            device_reuse_count=len(users_by_device[device] - {user}) if device else 0,
            is_device_missing=not bool(device),
            is_structuring_band=8000 <= amount < 10000 and row.transaction_type in {"TRANSFER", "WITHDRAWAL"},
            velocity_1h=float(len(recent)),
            user_amount_zscore=float(zscore),
            is_new_device_for_user=bool(device) and device not in devices_by_user[user],
        ))
        if device:
            users_by_device[device].add(user)
            devices_by_user[user].add(device)
        amounts_by_user[user].append(amount)
        recent_by_user[user].append(timestamp)
    return pd.DataFrame(vectors, columns=FEATURE_NAMES)


def _time_split(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    feature_frames, labels, split_indices, sources = [], [], [], []
    for source, source_frame in frame.groupby("source", sort=True):
        ordered = source_frame.sort_values("event_time", kind="stable").reset_index(drop=True)
        split = max(1, int(len(ordered) * 0.8))
        feature_frames.append(_features_for_source(ordered))
        labels.extend(ordered.is_fraud.astype(int).tolist())
        split_indices.extend([True] * split + [False] * (len(ordered) - split))
        sources.extend([source] * len(ordered))
    X = pd.concat(feature_frames, ignore_index=True).to_numpy(dtype=float)
    y = np.asarray(labels, dtype=int)
    train_mask = np.asarray(split_indices, dtype=bool)
    source_values = np.asarray(sources)
    summary = {source: int((source_values == source).sum()) for source in sorted(set(source_values))}
    return X[train_mask], X[~train_mask], y[train_mask], y[~train_mask], summary


def train_public_benchmarks(max_rows_per_source: int = 250_000, activate: bool = False) -> dict:
    paths = _download_kaggle_sources()
    data = pd.concat([
        _load_ieee(paths["ieee"], max_rows_per_source),
        _load_paysim(paths["paysim"], max_rows_per_source),
        _load_creditcard(paths["creditcard"], max_rows_per_source),
    ], ignore_index=True)
    data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=["amount", "event_time", "is_fraud"])
    X_train, X_test, y_train, y_test, source_counts = _time_split(data)
    if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
        raise RuntimeError("Each split needs both fraud and non-fraud examples; increase the source row cap.")

    classifier = XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.07, subsample=0.8,
        colsample_bytree=0.8, eval_metric="aucpr", random_state=RNG_SEED,
        scale_pos_weight=(y_train == 0).sum() / max(1, (y_train == 1).sum()),
    )
    classifier.fit(X_train, y_train)
    probabilities = classifier.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, predictions, average="binary", zero_division=0)
    metrics = {
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "average_precision": round(float(average_precision_score(y_test, probabilities)), 4),
        "precision": round(float(precision), 4), "recall": round(float(recall), 4), "f1": round(float(f1), 4),
    }
    anomaly_detector = IsolationForest(n_estimators=200, contamination=0.08, random_state=RNG_SEED).fit(X_train)
    fingerprint = hashlib.sha256(json.dumps({"rows": len(data), "sources": source_counts, "metrics": metrics}, sort_keys=True).encode()).hexdigest()[:12]
    version = f"public-benchmark-v1-{fingerprint}"
    version_dir = register_version(version)
    classifier_path, anomaly_path = version_dir / "risk_classifier.joblib", version_dir / "anomaly_detector.joblib"
    joblib.dump(classifier, classifier_path)
    joblib.dump(anomaly_detector, anomaly_path)
    reference = X_train[np.random.default_rng(RNG_SEED).choice(len(X_train), size=min(2000, len(X_train)), replace=False)]
    metadata = {
        "model_version": version, "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_data_source": "public_benchmarks_evaluation_only_v1", "can_be_production": False,
        "datasets": ["ieee-cis", "paysim", "creditcardfraud"], "source_row_counts": source_counts,
        "n_train": int(len(X_train)), "n_test": int(len(X_test)), "feature_names": FEATURE_NAMES,
        "split_method": "per-source chronological 80/20", "eval_metrics": metrics,
        "artifact_checksums": {"risk_classifier.joblib": hashlib.sha256(classifier_path.read_bytes()).hexdigest(), "anomaly_detector.joblib": hashlib.sha256(anomaly_path.read_bytes()).hexdigest()},
        "reference_distribution": {name: reference[:, index].round(4).tolist() for index, name in enumerate(FEATURE_NAMES)},
    }
    (version_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2))
    if activate:
        set_active_version(version)
    print(json.dumps({"model_version": version, "active": activate, "metrics": metrics, "rows": len(data)}, indent=2))
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-rows-per-source", type=int, default=250_000)
    parser.add_argument("--activate", action="store_true", help="Make the public-benchmark model active (not recommended).")
    args = parser.parse_args()
    train_public_benchmarks(args.max_rows_per_source, args.activate)
