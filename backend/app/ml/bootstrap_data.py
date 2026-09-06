"""Synthetic bootstrap dataset for the fraud risk classifier.

WHY THIS EXISTS
----------------
FinSecAI currently has no labeled fraud data. Public datasets (IEEE-CIS,
Kaggle Credit Card Fraud) cannot be used directly either: they are built on
feature sets (anonymized PCA components, card networks, browser fingerprints)
that do not exist in our production schema, which today is intentionally
minimal (amount, transaction_type, device_id). Training on their columns
would produce a model that cannot be fed with what upload_incidents actually
has available at inference time.

So this module generates synthetic transactions using the same feature
engineering as app.ml.features, with fraud-correlated structure based on
well-established fraud typologies.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRANSACTION_TYPES = ["TRANSFER", "WITHDRAWAL", "PAYMENT", "DEPOSIT"]
HIGH_AMOUNT_THRESHOLD = 20_000.0


def generate_bootstrap_dataset(n: int = 20_000, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic transaction dataset with an is_fraud label."""
    rng = np.random.default_rng(seed)

    transaction_type = rng.choice(
        TRANSACTION_TYPES,
        size=n,
        p=[0.40, 0.20, 0.30, 0.10],
    )

    base_mu = np.where(
        np.isin(transaction_type, ["TRANSFER", "WITHDRAWAL"]),
        8.5,
        7.2,
    )
    amount = rng.lognormal(mean=base_mu, sigma=1.1, size=n)
    amount = np.clip(amount, 50, 5_000_000)

    device_reuse_count = rng.choice(
        [0, 1, 2, 3, 5, 8, 15],
        size=n,
        p=[0.05, 0.70, 0.12, 0.06, 0.04, 0.02, 0.01],
    )
    is_device_missing = (rng.random(n) < 0.03).astype(int)
    device_reuse_count = np.where(
        is_device_missing == 1, 0, device_reuse_count)
    is_high_amount = (amount > HIGH_AMOUNT_THRESHOLD).astype(int)
    is_structuring_band = ((np.isin(transaction_type, ["TRANSFER", "WITHDRAWAL"])) &
                           (amount >= 8_000) & (amount < 10_000)).astype(int)
    velocity_1h = rng.poisson(1.2, size=n)
    burst_mask = rng.random(n) < 0.08
    velocity_1h[burst_mask] += rng.integers(5, 15, size=burst_mask.sum())
    user_amount_zscore = rng.normal(0, 1.0, size=n)
    is_new_device_for_user = (rng.random(n) < 0.12).astype(int)

    logit = (
        -4.2
        + 0.55 * np.log1p(device_reuse_count)
        + 1.8 * is_high_amount
        + 0.9 * np.isin(transaction_type,
                        ["TRANSFER", "WITHDRAWAL"]).astype(int)
        + 0.7 * is_device_missing
        + 1.0 * is_structuring_band
        + 0.18 * velocity_1h
        + 0.55 * np.maximum(user_amount_zscore, 0)
        + 0.8 * is_new_device_for_user
        + 0.4 * (np.log1p(amount) - np.log1p(amount).mean()) /
        np.log1p(amount).std()
        + rng.normal(0, 0.6, size=n)
    )
    fraud_prob = 1 / (1 + np.exp(-logit))
    is_fraud = (rng.random(n) < fraud_prob).astype(int)

    return pd.DataFrame(
        {
            "amount": amount,
            "transaction_type": transaction_type,
            "device_reuse_count": device_reuse_count,
            "is_device_missing": is_device_missing,
            "is_structuring_band": is_structuring_band,
            "velocity_1h": velocity_1h,
            "user_amount_zscore": user_amount_zscore,
            "is_new_device_for_user": is_new_device_for_user,
            "is_fraud": is_fraud,
        }
    )


if __name__ == "__main__":
    df = generate_bootstrap_dataset()
    print(df.describe(include="all"))
    print("\nFraud rate:", df["is_fraud"].mean())
