import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.metrics import build_metrics_frame, summarize_incident_query


def test_build_metrics_frame_is_deterministic_and_respects_period():
    now = datetime(2026, 7, 31, 12, 0, 0)

    frame = build_metrics_frame(now=now, points=12, period_minutes=60)

    assert len(frame) == 12
    assert frame["throughput_rps"].iloc[0] > 0
    assert frame["latency_p95_ms"].iloc[-1] >= frame["latency_p50_ms"].iloc[-1]
    assert frame["timestamp"].iloc[0] == now - timedelta(minutes=11)
    assert frame["timestamp"].iloc[-1] == now


def test_summarize_incident_query_returns_contextual_answer():
    incidents = pd.DataFrame(
        [
            {"incident_id": "INC-1", "risk_score": 0.92, "amount": 15000, "user_id": "U1"},
            {"incident_id": "INC-2", "risk_score": 0.21, "amount": 1200, "user_id": "U2"},
        ]
    )

    summary = summarize_incident_query("show me high risk transfers", incidents)

    assert summary["match_count"] == 1
    assert "INC-1" in summary["answer"]
    assert "high-risk" in summary["answer"]
