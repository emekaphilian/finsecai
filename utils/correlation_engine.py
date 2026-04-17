# paste the full feature_engineering.py code here

# utils/correlation_engine.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np
import pandas as pd

from .preprocessing import ensure_ts, parse_time_delta, save_df
from .risk_scoring import RuleEngine, RiskConfig, compute_combined_risk_score
from .feature_engineering import (
    FeatureConfig,
    build_basic_features_auth,
    build_basic_features_tx,
    build_basic_features_emp,
)

logger = logging.getLogger("finsec.correlation_engine")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
    logger.addHandler(ch)


@dataclass
class CorrEngineConfig:
    time_tolerance: str = "5m"
    high_value_tx_threshold: float = 10_000.0
    failed_login_threshold: int = 3
    output_dir: Path = field(default_factory=lambda: Path("data/processed"))
    risk_threshold: float = 0.7
    normalize_scores: bool = True
    drop_high_correlation: bool = False
    correlation_drop_threshold: float = 0.95
    random_seed: int = 42

    # Feature configs
    feature_config: FeatureConfig = field(default_factory=FeatureConfig)
    risk_config: RiskConfig = field(default_factory=RiskConfig)


# --------------------------
# Temporal correlation utils
# --------------------------
def temporal_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on_user: str = "user_id",
    time_left: str = "timestamp",
    time_right: str = "timestamp",
    tolerance: str = "5m",
) -> pd.DataFrame:
    """
    Pair events for the same user within +/- tolerance of timestamps.
    """
    left = ensure_ts(left, time_left).sort_values(time_left)
    right = ensure_ts(right, time_right).sort_values(time_right)
    tol = parse_time_delta(tolerance)

    merged = left.merge(right, on=on_user, suffixes=("_l", "_r"), how="inner", copy=False)
    merged["_tdiff"] = (merged[time_left] - merged[time_right]).abs()
    res = merged[merged["_tdiff"] <= tol].drop(columns=["_tdiff"])
    logger.debug("temporal_join -> %d rows", len(res))
    return res


# --------------------------
# Correlation / meta features
# --------------------------
def correlate_sources(
    df_auth: pd.DataFrame,
    df_tx: pd.DataFrame,
    df_emp: pd.DataFrame,
    cfg: CorrEngineConfig,
) -> pd.DataFrame:
    """
    Build features per source, join them temporally to generate meta-features,
    then produce a unified per-auth-anchor row suitable for scoring and alerts.
    """
    # Source-level features
    a = build_basic_features_auth(df_auth, cfg.feature_config)
    t = build_basic_features_tx(df_tx, cfg.feature_config)
    e = build_basic_features_emp(df_emp, cfg.feature_config)

    # Temporal correlations anchored on auth events
    a_t = temporal_join(a, t, tolerance=cfg.time_tolerance)
    a_e = temporal_join(a, e, tolerance=cfg.time_tolerance)

    # Meta-sequence flags
    a_t["failed_then_high_tx"] = (
        ((a_t.get("is_failed", 0) == 1) & (a_t.get("amount", 0) >= cfg.high_value_tx_threshold)).astype(int)
    )
    a_e["success_then_remote"] = (
        ((a_e.get("is_failed", 0) == 0) & (a_e.get("is_remote_access", 0) == 1)).astype(int)
    )

    # Anchor to the auth event (user_id + auth timestamp)
    a = a.copy()
    a["_auth_anchor"] = a["user_id"].astype(str) + "::" + a["timestamp"].astype(str)
    a_t["_auth_anchor"] = a_t["user_id"].astype(str) + "::" + a_t["timestamp_l"].astype(str)
    a_e["_auth_anchor"] = a_e["user_id"].astype(str) + "::" + a_e["timestamp_l"].astype(str)

    # Keep only non-overlapping columns when merging
    def drop_dupe_cols(base_cols: List[str], df_other: pd.DataFrame) -> pd.DataFrame:
        return df_other.drop(columns=[c for c in base_cols if c in df_other.columns], errors="ignore")

    merged = a.merge(drop_dupe_cols(list(a.columns), a_t), on="_auth_anchor", how="left", suffixes=("", "_tx"))
    merged = merged.merge(drop_dupe_cols(list(a.columns), a_e), on="_auth_anchor", how="left", suffixes=("", "_emp"))

    merged = merged.fillna(0)

    # Unified suspicious sequence indicator
    merged["suspicious_sequence"] = (
        (merged.get("failed_last_1h", 0) >= cfg.failed_login_threshold)
        | (merged.get("failed_then_high_tx", 0) == 1)
        | (merged.get("out_of_hours", 0) == 1)
        | (merged.get("tx_velocity_spike", 0) == 1)  # optional if present
    ).astype(int)

    # Initialize model outputs and rule columns
    merged["ml_fraud_score"] = 0.0
    merged["anomaly_score"] = 0.0
    merged["rule_hits"] = 0
    merged["rule_names"] = ""

    logger.info("Correlation produced %d unified rows", len(merged))
    return merged


# --------------------------
# ML wrapper helpers
# --------------------------
def fraud_model_predict_wrapper(model, df: pd.DataFrame) -> List[float]:
    """
    Best-effort scoring across various sklearn-like APIs:
      - predict_proba -> use class 1 probabilities
      - predict -> rank-normalized as proxy score
      - Fallback: heuristic combination of amount norm + failed_last_1h norm
    """
    features = df.select_dtypes(include=[float, int]).fillna(0)
    try:
        probs = model.predict_proba(features)
        if hasattr(probs, "ndim") and probs.ndim == 2 and probs.shape[1] >= 2:
            return probs[:, 1].tolist()
        return np.ravel(probs).tolist()
    except Exception:
        try:
            preds = model.predict(features)
            return pd.Series(preds).rank(pct=True).tolist()
        except Exception:
            amt = pd.to_numeric(df.get("amount", 0), errors="coerce").fillna(0.0)
            amt_norm = (amt - amt.min()) / (amt.max() - amt.min() + 1e-12)
            failed = pd.to_numeric(df.get("failed_last_1h", 0), errors="coerce").fillna(0.0)
            failed_norm = failed / (failed.max() + 1e-12)
            return (0.7 * amt_norm + 0.3 * failed_norm).tolist()


def anomaly_model_score_wrapper(model, df: pd.DataFrame) -> List[float]:
    """
    Best-effort anomaly scoring:
      - decision_function -> rank-normalized
      - score_samples -> rank-normalized
      - Fallback: z-score sum normalization
    """
    numeric = df.select_dtypes(include=[float, int]).fillna(0)
    try:
        scores = model.decision_function(numeric)
        return pd.Series(scores).rank(pct=True).tolist()
    except Exception:
        try:
            scores = model.score_samples(numeric)
            return pd.Series(scores).rank(pct=True).tolist()
        except Exception:
            z = ((numeric - numeric.mean()) / (numeric.std() + 1e-12)).abs().sum(axis=1)
            z_norm = (z - z.min()) / (z.max() - z.min() + 1e-12)
            return z_norm.tolist()


# --------------------------
# Pipeline runner
# --------------------------
def run_correlation_pipeline(
    df_auth: pd.DataFrame,
    df_tx: pd.DataFrame,
    df_emp: pd.DataFrame,
    cfg: Optional[CorrEngineConfig] = None,
    persist: bool = True,
    rule_engine: Optional[RuleEngine] = None,
    fraud_model=None,
    anomaly_model=None,
) -> Dict[str, Optional[Path]]:
    """
    Full pipeline:
      1) Feature engineering per source
      2) Temporal correlation to unify event context
      3) Rule evaluation
      4) Optional ML scoring
      5) Risk scoring and alert filtering
      6) Save artifacts (CSV)
    """
    if cfg is None:
        cfg = CorrEngineConfig()
    outdir = Path(cfg.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    unified = correlate_sources(df_auth, df_tx, df_emp, cfg)

    # Rules
    if rule_engine is None:
        rule_engine = RuleEngine()

    def _apply_rules(row):
        hits, names = rule_engine.evaluate(row)
        return hits, ";".join(names)

    res = unified.apply(lambda r: _apply_rules(r), axis=1, result_type="reduce")
    rule_hits = [t[0] for t in res]
    rule_names = [t[1] for t in res]
    unified["rule_hits"] = rule_hits
    unified["rule_names"] = rule_names

    # ML scoring hooks
    try:
        if fraud_model is not None:
            unified["ml_fraud_score"] = fraud_model_predict_wrapper(fraud_model, unified)
    except Exception as e:
        logger.warning("Fraud model failed: %s", e)
        unified["ml_fraud_score"] = 0.0

    try:
        if anomaly_model is not None:
            unified["anomaly_score"] = anomaly_model_score_wrapper(anomaly_model, unified)
    except Exception as e:
        logger.warning("Anomaly model failed: %s", e)
        unified["anomaly_score"] = 0.0

    # Risk scoring
    risk = compute_combined_risk_score(unified, cfg.risk_config)
    unified["risk_score"] = risk

    alerts = (
        unified[unified["risk_score"] >= cfg.risk_threshold]
        .sort_values("risk_score", ascending=False)
        .reset_index(drop=True)
    )

    artifacts: Dict[str, Optional[Path]] = {}
    if persist:
        artifacts["correlated_events"] = save_df(unified, outdir / "correlated_events.csv")
        artifacts["alerts"] = save_df(alerts, outdir / "alerts.csv")
    else:
        artifacts["correlated_events"] = None
        artifacts["alerts"] = None

    logger.info("Pipeline complete: %d alerts generated", len(alerts))
    return artifacts


if __name__ == "__main__":
    print("✓ correlation_engine.py executed successfully")
