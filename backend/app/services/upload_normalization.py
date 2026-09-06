import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd

_CANONICAL_COLUMNS = {
    "user_id": ["user_id", "customer_id", "customerid", "customer", "account_id", "account", "user"],
    "amount": ["amount", "txn_amount", "transaction_amount", "amount_usd", "value", "transactionvalue"],
    "transaction_type": ["transaction_type", "type", "txn_type", "tx_type", "transaction", "activity_type"],
    "device_id": ["device_id", "device", "deviceid", "device_name", "source_device", "client_device"],
    "transaction_time": ["transaction_time", "transaction_timestamp", "timestamp", "created_at", "event_time", "transaction_date"],
}


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).strip().lower())


def _canonical_for_column(column_name: str) -> str | None:
    normalized = _normalize_name(column_name)
    for canonical, aliases in _CANONICAL_COLUMNS.items():
        if normalized in {_normalize_name(alias) for alias in aliases}:
            return canonical
    return None


def _json_safe(value: Any) -> Any:
    """Convert pandas/NumPy and date values to JSON-compatible primitives."""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if pd.isna(value):
        return None
    return str(value)


def normalize_upload_dataframe(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Normalize upload column names to the internal canonical schema.

    The function also preserves each row's full original payload in a dedicated
    ``_raw_row`` column so downstream workflows can retain the untransformed
    values for future feature engineering or auditability.
    """

    normalized = frame.copy()
    column_map: dict[str, str] = {}

    for original_column in list(frame.columns):
        canonical = _canonical_for_column(original_column)
        if not canonical:
            continue
        if canonical not in normalized.columns:
            normalized[canonical] = frame[original_column]
        column_map[original_column] = canonical

    for column in ["user_id", "amount", "transaction_type", "device_id", "transaction_time"]:
        if column not in normalized.columns:
            normalized[column] = pd.NA

    normalized["_raw_row"] = [_json_safe(row.to_dict()) for _, row in frame.iterrows()]

    return normalized, column_map
