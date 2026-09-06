"""Model-evaluation math, ported from the original Streamlit prototype's
evaluation/metrics.py with the same formulas, operating on plain lists so it
has no Streamlit or pandas dependency at this layer.
"""

import numpy as np


def predict_labels(risk_scores: list[float], threshold: float = 0.5) -> list[int]:
    return [1 if s >= threshold else 0 for s in risk_scores]


def evaluate_classification(y_true: list[int], y_pred: list[int]) -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
    }


def fairness_by_segment(amounts: list[float], predictions: list[int], high_threshold: float = 5000) -> dict:
    segments: dict[str, dict] = {"high": {"pos": 0, "count": 0}, "low": {"pos": 0, "count": 0}}
    for amount, pred in zip(amounts, predictions):
        seg = "high" if amount >= high_threshold else "low"
        segments[seg]["count"] += 1
        segments[seg]["pos"] += pred

    return {
        seg: {
            "positive_rate": round(data["pos"] / data["count"], 3) if data["count"] else 0.0,
            "count": data["count"],
        }
        for seg, data in segments.items()
    }


def compute_drift(baseline: list[int], current: list[int]) -> dict:
    """Population Stability Index between two prediction batches."""
    b_rate = np.mean(baseline) if baseline else 0.0
    c_rate = np.mean(current) if current else 0.0
    eps = 1e-6
    b_rate, c_rate = max(b_rate, eps), max(c_rate, eps)

    psi = (c_rate - b_rate) * np.log(c_rate / b_rate)
    psi += (1 - c_rate + eps - (1 - b_rate + eps)) * np.log((1 - c_rate + eps) / (1 - b_rate + eps))
    psi = abs(round(float(psi), 4))

    status = "low" if psi < 0.05 else "medium" if psi < 0.1 else "high"
    return {"drift_score": psi, "mean_shift": round(float(c_rate - b_rate), 3), "status": status}


def calibration_curve(y_true: list[int], confidences: list[float], bins: int = 10) -> list[dict]:
    edges = np.linspace(0, 1, bins + 1)
    points = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        idx = [j for j, c in enumerate(confidences) if lo <= c < hi or (i == bins - 1 and c == hi)]
        if not idx:
            continue
        avg_conf = float(np.mean([confidences[j] for j in idx]))
        avg_true = float(np.mean([y_true[j] for j in idx]))
        points.append({"bucket": round(avg_conf, 2), "observed": round(avg_true, 2), "count": len(idx)})
    return points


def governance_compliance(flag_lists: list[list[str]]) -> dict:
    critical = sum(1 for flags in flag_lists if flags)
    total = len(flag_lists) or 1
    critical_rate = critical / total
    status = "compliant" if critical_rate < 0.1 else "review_needed" if critical_rate < 0.3 else "non_compliant"
    return {"compliance_status": status, "critical_rate": round(critical_rate, 3)}
