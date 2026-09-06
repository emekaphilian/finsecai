from datetime import datetime, timedelta
from typing import Any, Dict

import numpy as np
import pandas as pd


def build_metrics_frame(now: datetime | None = None, points: int = 60, period_minutes: int = 60) -> pd.DataFrame:
    """Create deterministic metrics data for the dashboard."""
    if now is None:
        now = datetime.now()

    points = max(2, int(points))
    timestamps = [now - timedelta(minutes=(points - 1 - idx)) for idx in range(points)]
    idx = np.arange(points)

    throughput_rps = 105 + 12 * np.sin(idx / 4) + 0.6 * idx
    latency_p50_ms = 45 + 6 * np.cos(idx / 5) + 0.35 * idx
    latency_p95_ms = latency_p50_ms + 80 + 8 * np.sin(idx / 3)
    latency_p99_ms = latency_p95_ms + 90 + 7 * np.cos(idx / 4)
    error_rate_pct = np.clip(0.25 + 0.08 * np.abs(np.sin(idx / 3)) + 0.004 * idx, 0.1, 1.2)
    cache_hit_rate_pct = np.clip(76 - 3 * np.sin(idx / 6) - 0.1 * idx, 60, 90)
    cpu_usage_pct = np.clip(35 + 10 * np.sin(idx / 3) + 0.4 * idx, 20, 85)
    memory_usage_pct = np.clip(48 + 6 * np.cos(idx / 4) + 0.2 * idx, 35, 78)
    db_connections_active = np.clip(8 + 2 * np.sin(idx / 2) + idx // 4, 5, 18)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "throughput_rps": throughput_rps,
            "latency_p50_ms": latency_p50_ms,
            "latency_p95_ms": latency_p95_ms,
            "latency_p99_ms": latency_p99_ms,
            "error_rate_pct": error_rate_pct,
            "cache_hit_rate_pct": cache_hit_rate_pct,
            "cpu_usage_pct": cpu_usage_pct,
            "memory_usage_pct": memory_usage_pct,
            "db_connections_active": db_connections_active,
        }
    )


def summarize_incident_query(query: str, incidents: pd.DataFrame) -> Dict[str, Any]:
    """Answer a simple natural-language incident query."""
    query_text = (query or "").strip().lower()
    incidents = incidents.copy()

    if "high risk" in query_text or "high-risk" in query_text or "suspicious" in query_text:
        threshold = 0.8
        mask = incidents.get("risk_score", pd.Series([0])) >= threshold
    elif "high value" in query_text or "large" in query_text or "amount" in query_text:
        threshold = 10000
        mask = incidents.get("amount", pd.Series([0])) >= threshold
    else:
        threshold = 0.5
        mask = incidents.get("risk_score", pd.Series([0])) >= threshold

    matches = incidents.loc[mask]
    if matches.empty:
        return {
            "answer": "No incidents matched your query yet. Try asking for high-risk transfers or large-value events.",
            "match_count": 0,
            "threshold": threshold,
        }

    top_incident = matches.iloc[0]
    top_incident_id = str(top_incident.get("incident_id", "unknown"))
    answer = (
        f"Found {len(matches)} high-risk incident(s) matching your query. "
        f"The highest-priority case is {top_incident_id} with a risk score of {top_incident.get('risk_score', 0):.2f}."
    )
    return {
        "answer": answer,
        "match_count": int(len(matches)),
        "threshold": threshold,
        "matches": matches.to_dict("records"),
    }
