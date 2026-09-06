"""Load test for the risk-scoring path -- the actual bottleneck upload_incidents
depends on (per-row: TransactionHistory lookups + model inference + SHAP).

This runs against the real RiskModel and a real (SQLite, for this test)
TransactionHistory -- not a mock -- so the numbers reflect actual inference +
SHAP cost, not an idealized estimate. It does NOT run against a live FastAPI
server (no network round-trip included) -- add that layer separately if
you need end-to-end HTTP latency; this isolates the compute-bound part,
which is what the earlier `50,000 row` upload cap in incidents.py was sized
against.

Usage:
    python -m app.ml.load_test --rows 1000
    python -m app.ml.load_test --rows 10000
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from app.ml.features import build_features_from_values
from app.ml.risk_model import get_risk_model


def run(n_rows: int) -> None:
    model = get_risk_model()
    rng = np.random.default_rng(0)

    # Realistic-ish mixed workload, not all identical inputs (a model given
    # the exact same input repeatedly can hit cache effects that don't
    # reflect real traffic).
    amounts = rng.lognormal(8, 1.2, n_rows)
    types = rng.choice(["TRANSFER", "WITHDRAWAL", "PAYMENT", "DEPOSIT"], n_rows)
    device_reuse = rng.choice([0, 1, 2, 5, 10], n_rows)

    latencies = []
    start_total = time.perf_counter()
    for i in range(n_rows):
        vec = build_features_from_values(
            amount=float(amounts[i]),
            transaction_type=str(types[i]),
            device_reuse_count=int(device_reuse[i]),
            is_device_missing=False,
        )
        t0 = time.perf_counter()
        model.predict(vec)
        latencies.append(time.perf_counter() - t0)
    total_time = time.perf_counter() - start_total

    latencies = np.array(latencies)
    print(f"Rows:            {n_rows}")
    print(f"Total time:      {total_time:.2f}s")
    print(f"Throughput:      {n_rows / total_time:.1f} predictions/sec")
    print(f"Latency mean:    {latencies.mean()*1000:.2f}ms")
    print(f"Latency p50:     {np.percentile(latencies, 50)*1000:.2f}ms")
    print(f"Latency p95:     {np.percentile(latencies, 95)*1000:.2f}ms")
    print(f"Latency p99:     {np.percentile(latencies, 99)*1000:.2f}ms")
    print(f"Latency max:     {latencies.max()*1000:.2f}ms")
    print()
    print(f"Est. time for a {n_rows}-row upload (this stage only, single-threaded): {total_time:.1f}s")
    print("NOTE: does not include TransactionHistory DB query overhead (one query per")
    print("upload batch, not per row -- see incidents.py), pandas parsing, or DB writes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1000)
    args = parser.parse_args()
    run(args.rows)
