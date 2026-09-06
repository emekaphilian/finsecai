"""Minimal Prometheus-compatible metrics.

Deliberately small: four metrics that answer the operational questions that
actually come up for a fraud model in production --
    - Is it being called, and how often? (predictions_total)
    - Is it fast enough? (prediction_latency_seconds)
    - Is its output distribution reasonable, or has something gone wrong
      upstream (e.g. everything suddenly scoring 0.99)? (risk_score
      distribution, via the same histogram's bucket counts)
    - Which model version is actually live right now? (active_model_version,
      a labeled gauge -- lets a dashboard show "which model produced this
      traffic" without cross-referencing logs)

Not building a general-purpose metrics framework here -- add specific
metrics as specific operational questions come up, rather than
instrumenting speculatively.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

predictions_total = Counter(
    "finsecai_predictions_total",
    "Total number of risk model predictions served",
    ["model_version"],
)

prediction_latency_seconds = Histogram(
    "finsecai_prediction_latency_seconds",
    "Time to produce one risk model prediction (feature build + inference + SHAP)",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

risk_score_distribution = Histogram(
    "finsecai_risk_score",
    "Distribution of risk scores produced by the model -- a sudden shift here "
    "(e.g. everything clustering near 0 or 1) is often visible before drift "
    "metrics catch up, and is cheap to watch on a dashboard.",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

active_model_version = Gauge(
    "finsecai_active_model_version_info",
    "Always 1; the model_version label identifies which version is currently active",
    ["model_version"],
)


def record_prediction(model_version: str, risk_score: float, latency_seconds: float) -> None:
    predictions_total.labels(model_version=model_version).inc()
    prediction_latency_seconds.observe(latency_seconds)
    risk_score_distribution.observe(risk_score)


def set_active_model_version_metric(model_version: str) -> None:
    # Gauge with a label used as an "info" pattern: clear old label values
    # first so a rollback doesn't leave two versions both showing as "active"
    # in whatever scraped the metric before the switch.
    active_model_version.clear()
    active_model_version.labels(model_version=model_version).set(1)


def metrics_response() -> tuple[bytes, str]:
    """Returns (body, content_type) for a /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
