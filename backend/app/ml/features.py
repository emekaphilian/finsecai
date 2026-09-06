"""Shared, online/offline fraud feature engineering."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import Incident

TRANSACTION_TYPES = ["TRANSFER", "WITHDRAWAL", "PAYMENT", "DEPOSIT"]
HIGH_AMOUNT_THRESHOLD = 20_000.0
# A deliberately configurable band below the common reporting threshold.  This
# is a signal, not a declaration that a transaction is illicit.
STRUCTURING_BAND_MIN = 8_000.0
STRUCTURING_BAND_MAX = 10_000.0

FEATURE_NAMES = [
    "log_amount",
    "is_transfer",
    "is_withdrawal",
    "is_payment",
    "is_deposit",
    "device_reuse_count",
    "is_device_missing",
    "is_high_amount",
    "is_structuring_band",
    "velocity_1h",
    "user_amount_zscore",
    "is_new_device_for_user",
]


def _encode(
    amount: float,
    transaction_type: str,
    device_reuse_count: int,
    is_device_missing: bool,
    is_structuring_band: bool = False,
    velocity_1h: float = 0.0,
    user_amount_zscore: float = 0.0,
    is_new_device_for_user: bool = False,
) -> list[float]:
    tx = (transaction_type or "").upper()
    return [
        math.log1p(max(0.0, amount)),
        1.0 if tx == "TRANSFER" else 0.0,
        1.0 if tx == "WITHDRAWAL" else 0.0,
        1.0 if tx == "PAYMENT" else 0.0,
        1.0 if tx == "DEPOSIT" else 0.0,
        float(device_reuse_count),
        1.0 if is_device_missing else 0.0,
        1.0 if amount > HIGH_AMOUNT_THRESHOLD else 0.0,
        1.0 if is_structuring_band else 0.0,
        float(velocity_1h),
        float(user_amount_zscore),
        1.0 if is_new_device_for_user else 0.0,
    ]


def build_features_from_values(
    amount: float,
    transaction_type: str,
    device_reuse_count: int,
    is_device_missing: bool,
    is_structuring_band: bool = False,
    velocity_1h: float = 0.0,
    user_amount_zscore: float = 0.0,
    is_new_device_for_user: bool = False,
) -> list[float]:
    return _encode(
        amount, transaction_type, device_reuse_count, is_device_missing,
        is_structuring_band, velocity_1h, user_amount_zscore,
        is_new_device_for_user,
    )


class TransactionHistory:
    """Tenant-scoped state for cross-user devices and per-user behaviour."""

    def __init__(self, db: Session, tenant_id: str):
        self._by_device: dict[str, set[str]] = {}
        self._devices_by_user: dict[str, set[str]] = {}
        self._amounts_by_user: dict[str, list[float]] = {}
        self._recent_by_user: dict[str, list[datetime]] = {}
        cutoff = datetime.utcnow() - timedelta(hours=1)
        rows = db.query(
            Incident.device_id, Incident.user_id, Incident.amount,
            Incident.created_at,
        ).filter(Incident.tenant_id == tenant_id).all()
        for device_id, user_id, amount, created_at in rows:
            if device_id:
                self._by_device.setdefault(device_id, set()).add(user_id)
                self._devices_by_user.setdefault(user_id, set()).add(device_id)
            self._amounts_by_user.setdefault(user_id, []).append(float(amount))
            if created_at and created_at >= cutoff:
                self._recent_by_user.setdefault(user_id, []).append(created_at)

    def reuse_count(self, device_id: str, user_id: str) -> int:
        return len(self._by_device.get(device_id, set()) - {user_id}) if device_id else 0

    def is_new_device_for_user(self, device_id: str, user_id: str) -> bool:
        return bool(device_id) and device_id not in self._devices_by_user.get(user_id, set())

    def velocity_1h(self, user_id: str) -> float:
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent = [at for at in self._recent_by_user.get(user_id, []) if at >= cutoff]
        self._recent_by_user[user_id] = recent
        return float(len(recent))

    def user_amount_zscore(self, user_id: str, amount: float) -> float:
        amounts = self._amounts_by_user.get(user_id, [])
        if len(amounts) < 2:
            return 0.0
        mean = sum(amounts) / len(amounts)
        variance = sum((value - mean) ** 2 for value in amounts) / len(amounts)
        stddev = math.sqrt(variance)
        return (amount - mean) / stddev if stddev > 0 else 0.0

    def observe(self, device_id: str, user_id: str, amount: float) -> None:
        if device_id:
            self._by_device.setdefault(device_id, set()).add(user_id)
            self._devices_by_user.setdefault(user_id, set()).add(device_id)
        self._amounts_by_user.setdefault(user_id, []).append(float(amount))
        self._recent_by_user.setdefault(user_id, []).append(datetime.utcnow())


# Existing integrations may import this old name.
DeviceHistory = TransactionHistory


def build_features_for_row(
    transaction_history: TransactionHistory,
    user_id: str,
    amount: float,
    transaction_type: str,
    device_id: str,
) -> tuple[list[float], dict[str, float]]:
    structured = STRUCTURING_BAND_MIN <= amount < STRUCTURING_BAND_MAX and (
        transaction_type or "").upper() in {"TRANSFER", "WITHDRAWAL"}
    vector = _encode(
        amount, transaction_type,
        transaction_history.reuse_count(device_id, user_id), not bool(device_id),
        is_structuring_band=structured,
        velocity_1h=transaction_history.velocity_1h(user_id),
        user_amount_zscore=transaction_history.user_amount_zscore(user_id, amount),
        is_new_device_for_user=transaction_history.is_new_device_for_user(device_id, user_id),
    )
    return vector, dict(zip(FEATURE_NAMES, vector))
