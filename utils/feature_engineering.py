# paste the full feature_engineering.py code here

# utils/feature_engineering.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("finsec.feature_engineering")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
    logger.addHandler(ch)


@dataclass
class FeatureConfig:
    # Time-of-day ranges for "out-of-hours"
    business_hours_start: int = 8   # 08:00
    business_hours_end: int = 18    # 18:00
    # Transaction thresholds
    high_value_threshold: float = 10_000.0
    tx_velocity_window: str = "1h"
    auth_failure_window: str = "1h"
    emp_remote_keywords: Tuple[str, ...] = ("vpn", "remote", "rdp")
    # Normalization toggles
    normalize_numeric: bool = True


def _safe_bool(x) -> int:
    if pd.isna(x):
        return 0
    try:
        # Accept True/False, "true"/"false", 1/0
        return int(str(x).strip().lower() in ("1", "true", "t", "yes", "y"))
    except Exception:
        return 0


def _normalize_series(s: pd.Series) -> pd.Series:
    s = s.astype(float)
    rng = s.max() - s.min()
    if rng == 0 or not np.isfinite(rng):
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (rng + 1e-12)


def _flag_out_of_hours(ts: pd.Series, start: int, end: int) -> pd.Series:
    hours = ts.dt.hour
    return ((hours < start) | (hours >= end)).astype(int)


def build_basic_features_auth(df_auth: pd.DataFrame, cfg: Optional[FeatureConfig] = None) -> pd.DataFrame:
    """
    Build authentication features:
      - is_failed
      - out_of_hours
      - failed_last_1h (rolling per-user)
      - auth_event_rate_1h
      - device_diversity_24h
      - ip_diversity_24h
    Required columns: user_id, timestamp, success, ip, device_id
    """
    if cfg is None:
        cfg = FeatureConfig()

    df = df_auth.copy()
    if "timestamp" not in df.columns:
        raise ValueError("Authentication dataframe must contain 'timestamp'.")
    if "user_id" not in df.columns:
        raise ValueError("Authentication dataframe must contain 'user_id'.")

    # Canonicals
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

    # Basic flags
    df["is_failed"] = df.get("success", 1).apply(lambda x: 1 - _safe_bool(x))
    df["out_of_hours"] = _flag_out_of_hours(df["timestamp"], cfg.business_hours_start, cfg.business_hours_end)

    # Rolling failures per user in last auth_failure_window
    df["failed_last_1h"] = (
        df.set_index("timestamp")
          .groupby("user_id")["is_failed"]
          .rolling(cfg.auth_failure_window).sum()
          .reset_index(level=0, drop=True)
          .fillna(0)
          .astype(int)
    )

    # Event rate (count) per 1h window
    df["auth_event_rate_1h"] = (
        df.assign(event=1)
          .set_index("timestamp")
          .groupby("user_id")["event"]
          .rolling(cfg.auth_failure_window).sum()
          .reset_index(level=0, drop=True)
          .fillna(0)
    )

    # Diversity features (unique devices/IPs in 24h rolling)
    window24h = "24h"
    for col, newcol in [("device_id", "device_diversity_24h"), ("ip", "ip_diversity_24h")]:
        if col in df.columns:
            df[newcol] = (
                df.set_index("timestamp")
                  .groupby("user_id")[col]
                  .rolling(window24h).apply(lambda x: x.nunique(), raw=False)
                  .reset_index(level=0, drop=True)
                  .fillna(0)
            )
        else:
            df[newcol] = 0

    # Normalization (optional)
    if cfg.normalize_numeric:
        for col in ["failed_last_1h", "auth_event_rate_1h", "device_diversity_24h", "ip_diversity_24h"]:
            df[f"{col}_norm"] = _normalize_series(df[col])

    logger.debug("Auth features built: %d rows", len(df))
    return df


def build_basic_features_tx(df_tx: pd.DataFrame, cfg: Optional[FeatureConfig] = None) -> pd.DataFrame:
    """
    Build transaction features:
      - high_value
      - amount_norm
      - tx_velocity_amount_1h
      - tx_velocity_count_1h
      - country_switch_rate_24h
    Required columns: user_id, timestamp, amount, country
    """
    if cfg is None:
        cfg = FeatureConfig()

    df = df_tx.copy()
    if "timestamp" not in df.columns:
        raise ValueError("Transaction dataframe must contain 'timestamp'.")
    if "user_id" not in df.columns:
        raise ValueError("Transaction dataframe must contain 'user_id'.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

    # Basic numeric
    df["amount"] = pd.to_numeric(df.get("amount", 0), errors="coerce").fillna(0.0)
    df["high_value"] = (df["amount"] >= cfg.high_value_threshold).astype(int)

    # Velocity features over 1h window
    df["tx_velocity_amount_1h"] = (
        df.set_index("timestamp")
          .groupby("user_id")["amount"]
          .rolling(cfg.tx_velocity_window).sum()
          .reset_index(level=0, drop=True)
          .fillna(0.0)
    )
    df["tx_velocity_count_1h"] = (
        df.assign(event=1)
          .set_index("timestamp")
          .groupby("user_id")["event"]
          .rolling(cfg.tx_velocity_window).sum()
          .reset_index(level=0, drop=True)
          .fillna(0.0)
    )

    # Country switch rate over 24h (fraction of consecutive txs changing country)
    if "country" in df.columns:
        g = df.groupby("user_id")
        # mark change points
        df["country_change"] = g["country"].shift(1).ne(df["country"]).astype(int)
        df["country_switch_rate_24h"] = (
            df.set_index("timestamp")
              .groupby("user_id")["country_change"]
              .rolling("24h").mean()
              .reset_index(level=0, drop=True)
              .fillna(0.0)
        )
    else:
        df["country_switch_rate_24h"] = 0.0

    # Normalization
    if cfg.normalize_numeric:
        for col in ["amount", "tx_velocity_amount_1h", "tx_velocity_count_1h"]:
            df[f"{col}_norm"] = _normalize_series(df[col])

    logger.debug("Transaction features built: %d rows", len(df))
    return df


def build_basic_features_emp(df_emp: pd.DataFrame, cfg: Optional[FeatureConfig] = None) -> pd.DataFrame:
    """
    Build employee access features:
      - is_remote_access (keyword-based)
      - access_out_of_hours
      - resource_access_rate_1h
      - location_entropy_24h (approx via unique count)
      - privilege_level_num (optional mapping if 'privilege_level' exists)
    Required columns: user_id, timestamp, resource, access_type, location
    """
    if cfg is None:
        cfg = FeatureConfig()

    df = df_emp.copy()
    if "timestamp" not in df.columns:
        raise ValueError("Employee access dataframe must contain 'timestamp'.")
    if "user_id" not in df.columns:
        raise ValueError("Employee access dataframe must contain 'user_id'.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

    # Remote access heuristics
    access_type = df.get("access_type")
    if access_type is not None:
        lowered = access_type.fillna("").astype(str).str.lower()
        df["is_remote_access"] = lowered.apply(
            lambda x: int(any(k in x for k in cfg.emp_remote_keywords))
        )
    else:
        df["is_remote_access"] = 0

    # Out-of-hours
    df["access_out_of_hours"] = _flag_out_of_hours(df["timestamp"], cfg.business_hours_start, cfg.business_hours_end)

    # Resource access rate
    df["resource_access_rate_1h"] = (
        df.assign(event=1)
          .set_index("timestamp")
          .groupby("user_id")["event"]
          .rolling("1h").sum()
          .reset_index(level=0, drop=True)
          .fillna(0.0)
    )

    # Location diversity (proxy for entropy)
    if "location" in df.columns:
        df["location_diversity_24h"] = (
            df.set_index("timestamp")
              .groupby("user_id")["location"]
              .rolling("24h").apply(lambda x: x.nunique(), raw=False)
              .reset_index(level=0, drop=True)
              .fillna(0.0)
        )
    else:
        df["location_diversity_24h"] = 0.0

    # Optional privilege mapping
    if "privilege_level" in df.columns:
        levels = df["privilege_level"].fillna("").astype(str).str.lower()
        map_ = {"low": 0, "standard": 1, "high": 2, "admin": 3}
        df["privilege_level_num"] = levels.map(map_).fillna(1).astype(int)
    else:
        df["privilege_level_num"] = 1

    # Normalization
    if cfg.normalize_numeric:
        for col in ["resource_access_rate_1h", "location_diversity_24h", "privilege_level_num"]:
            df[f"{col}_norm"] = _normalize_series(df[col])

    logger.debug("Employee features built: %d rows", len(df))
    return df


def engineer_features(df: pd.DataFrame, cfg: Optional[FeatureConfig] = None) -> pd.DataFrame:
    """
    Wrapper function to apply feature engineering to generic dataframes.
    Attempts to detect the type of data and apply appropriate feature engineering.
    
    Args:
        df: Input dataframe
        cfg: Feature engineering configuration
        
    Returns:
        Dataframe with engineered features
    """
    if cfg is None:
        cfg = FeatureConfig()
    
    df = df.copy()
    
    # Try to apply transaction features if appropriate columns exist
    if 'amount' in df.columns or 'transaction_type' in df.columns:
        try:
            df = build_basic_features_tx(df, cfg)
        except Exception as e:
            logger.warning(f"Could not apply TX features: {e}")
    
    # Try to apply authentication features if appropriate columns exist
    if 'login_success' in df.columns or 'auth_method' in df.columns:
        try:
            df = build_basic_features_auth(df, cfg)
        except Exception as e:
            logger.warning(f"Could not apply Auth features: {e}")
    
    # Ensure common expected features exist
    expected_features = ['txn_velocity', 'avg_amount_historical', 'amount_volatility']
    for feat in expected_features:
        if feat not in df.columns:
            df[feat] = 0.0  # Fill with defaults if not created
    
    logger.debug("Features engineered: %d rows, %d columns", len(df), len(df.columns))
    return df

