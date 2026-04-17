# paste the full feature_engineering.py code here

# utils/preprocessing.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, List

import pandas as pd
import numpy as np

logger = logging.getLogger("finsec.preprocessing")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
    logger.addHandler(ch)


def ensure_ts(df: pd.DataFrame, col: str = "timestamp") -> pd.DataFrame:
    """
    Ensure column is datetime; rows with non-coercible timestamps remain as NaT.
    """
    df = df.copy()
    df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def parse_time_delta(s: str) -> pd.Timedelta:
    """
    Parse strings like '5m', '1h', '24h' into pandas Timedelta.
    """
    return pd.to_timedelta(s)


def save_df(df: pd.DataFrame, path: Path) -> Path:
    """
    Save dataframe to CSV, creating parent directories if needed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved dataframe: %s (%d rows)", path, len(df))
    return path


def standardize_columns(df: pd.DataFrame, col_map: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Rename columns according to col_map, lower-case and strip spaces for all columns.
    """
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    if col_map:
        df = df.rename(columns=col_map)
    return df


def coerce_types(df: pd.DataFrame, numeric_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Coerce numeric columns to numeric types; fill NaNs with 0.0 for numeric columns.
    """
    df = df.copy()
    if numeric_cols:
        for c in numeric_cols:
            df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0.0)
    return df


def clean_dataframe(
    df: pd.DataFrame,
    timestamp_col: str = "timestamp",
    sort_cols: Optional[List[str]] = None,
    drop_duplicates: bool = True,
) -> pd.DataFrame:
    """
    Generic cleaning: ensure timestamp, sort, and deduplicate.
    """
    df = ensure_ts(df, timestamp_col)
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)
    else:
        df = df.sort_values(timestamp_col).reset_index(drop=True)
    if drop_duplicates:
        df = df.drop_duplicates().reset_index(drop=True)
    return df


def align_user_column(df: pd.DataFrame, candidates: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Ensure a 'user_id' column exists by auto-mapping common alternatives.
    """
    df = df.copy()
    if "user_id" in df.columns:
        return df
    if candidates is None:
        candidates = ["user", "userid", "account_id", "employee_id", "customer_id"]
    for c in candidates:
        if c in df.columns:
            df["user_id"] = df[c]
            return df
    raise ValueError("No user identifier column found; expected one of: 'user_id', 'user', 'userid', 'account_id', 'employee_id', 'customer_id'.")


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main preprocessing wrapper that applies standard cleaning and preparation.
    
    Args:
        df: Input dataframe with raw data
        
    Returns:
        Preprocessed dataframe ready for feature engineering
    """
    df = df.copy()
    
    # Ensure timestamp column exists and is datetime
    if 'timestamp' in df.columns:
        df = ensure_ts(df, 'timestamp')
    
    # Align user_id column
    try:
        df = align_user_column(df)
    except ValueError:
        logger.warning("Could not align user column, proceeding without")
    
    # Standardize column names
    df = standardize_columns(df)
    
    # Coerce numeric columns
    numeric_cols = ['amount', 'risk_score', 'txn_velocity', 'avg_amount_historical', 'amount_volatility']
    df = coerce_types(df, [col for col in numeric_cols if col in df.columns])
    
    # Clean dataframe (remove duplicates, handle missing values)
    df = clean_dataframe(df)
    
    logger.info("Data preprocessing complete: %d rows, %d columns", len(df), len(df.columns))
    return df