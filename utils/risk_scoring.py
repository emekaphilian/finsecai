# paste the full feature_engineering.py code here

# utils/risk_scoring.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("finsec.risk_scoring")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
    logger.addHandler(ch)


@dataclass
class RiskConfig:
    # Base weights (tune as needed)
    w_ml_fraud: float = 0.45
    w_anomaly: float = 0.25
    w_rules: float = 0.20
    w_sequence: float = 0.10
    # Rule hit normalization
    max_rule_hits: int = 5
    # Clipping bounds
    min_score: float = 0.0
    max_score: float = 1.0
    normalize_inputs: bool = True


class RuleEngine:
    """
    Simple rule engine. Add/modify rules as needed. Each rule takes a row and returns (bool, 'rule_name').
    """
    def __init__(self):
        self.rules = [
            self.rule_failed_logins_burst,
            self.rule_high_value_after_failure,
            self.rule_out_of_hours_sensitive_access,
            self.rule_remote_access_with_privilege,
            self.rule_tx_velocity_spike,
        ]

    def evaluate(self, row: pd.Series) -> Tuple[int, List[str]]:
        hits = 0
        names: List[str] = []
        for fn in self.rules:
            ok, name = fn(row)
            if ok:
                hits += 1
                names.append(name)
        return hits, names

    # --- Rules ---
    @staticmethod
    def rule_failed_logins_burst(row: pd.Series) -> Tuple[bool, str]:
        thr = 3
        return (int(row.get("failed_last_1h", 0)) >= thr, "failed_logins_burst")

    @staticmethod
    def rule_high_value_after_failure(row: pd.Series) -> Tuple[bool, str]:
        # Use the correlated meta feature if present, else raw amount
        hv = float(row.get("amount", 0.0)) >= 10_000.0
        failed = int(row.get("is_failed", 0)) == 1 or int(row.get("failed_then_high_tx", 0)) == 1
        return (hv and failed, "failed_then_high_value_tx")

    @staticmethod
    def rule_out_of_hours_sensitive_access(row: pd.Series) -> Tuple[bool, str]:
        out = int(row.get("out_of_hours", 0)) == 1 or int(row.get("access_out_of_hours", 0)) == 1
        sensitive = str(row.get("resource", "")).lower()
        is_sensitive = any(k in sensitive for k in ("prod", "payroll", "finance", "db", "pii"))
        return (out and is_sensitive, "out_of_hours_sensitive_access")

    @staticmethod
    def rule_remote_access_with_privilege(row: pd.Series) -> Tuple[bool, str]:
        remote = int(row.get("is_remote_access", 0)) == 1
        priv = int(row.get("privilege_level_num", 1)) >= 2
        return (remote and priv, "remote_access_privileged")

    @staticmethod
    def rule_tx_velocity_spike(row: pd.Series) -> Tuple[bool, str]:
        vel_amt = float(row.get("tx_velocity_amount_1h", 0.0))
        vel_cnt = float(row.get("tx_velocity_count_1h", 0.0))
        # Heuristic thresholds
        return ((vel_amt >= 25_000.0) or (vel_cnt >= 10.0), "tx_velocity_spike")


def _norm(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").fillna(0.0)
    rng = s.max() - s.min()
    if rng == 0 or not np.isfinite(rng):
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (rng + 1e-12)


def compute_combined_risk_score(df: pd.DataFrame, cfg: RiskConfig) -> pd.Series:
    """
    Combine ML scores, rules, and sequences into unified risk score in [0,1].
    Expected columns (best-effort):
      - ml_fraud_score [0..1]
      - anomaly_score [0..1]
      - rule_hits (int)
      - suspicious_sequence (0/1)
    """
    x_ml = df.get("ml_fraud_score", 0.0)
    x_anom = df.get("anomaly_score", 0.0)
    x_rules = df.get("rule_hits", 0)
    x_seq = df.get("suspicious_sequence", 0)

    if cfg.normalize_inputs:
        x_ml = _norm(pd.Series(x_ml))
        x_anom = _norm(pd.Series(x_anom))
        x_rules = pd.Series(x_rules).clip(0, cfg.max_rule_hits) / max(cfg.max_rule_hits, 1)
        x_seq = pd.Series(x_seq).clip(0, 1)

    score = (
        cfg.w_ml_fraud * x_ml
        + cfg.w_anomaly * x_anom
        + cfg.w_rules * x_rules
        + cfg.w_sequence * x_seq
    )

    return pd.Series(np.clip(score.astype(float), cfg.min_score, cfg.max_score), index=df.index)
