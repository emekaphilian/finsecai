import hashlib

import pandas as pd
import pytest
from fastapi import HTTPException


class MemoryRedis:
    def __init__(self):
        self.values = {}
        self.expirations = {}

    def incr(self, key):
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key, seconds):
        self.expirations[key] = seconds

    def ttl(self, key):
        return self.expirations.get(key, -1)


def test_rate_limit_blocks_after_limit_and_returns_retry_after(monkeypatch):
    from app.core import rate_limit

    memory_redis = MemoryRedis()
    monkeypatch.setattr(rate_limit, "get_redis", lambda: memory_redis)
    for _ in range(10):
        rate_limit._check_and_increment("test", limit=10, window_seconds=60)
    with pytest.raises(HTTPException) as exc:
        rate_limit._check_and_increment("test", limit=10, window_seconds=60)
    assert exc.value.status_code == 429
    assert exc.value.headers["Retry-After"] == "60"


def test_invalid_upload_rows_are_rejected_or_safely_truncated():
    from app.api.routes.incidents import MAX_STRING_FIELD_LEN, _validate_row

    for row in (
        pd.Series({"user_id": "", "amount": 1}),
        pd.Series({"user_id": "u", "amount": float("nan")} ),
        pd.Series({"user_id": "u", "amount": -1}),
        pd.Series({"user_id": "u", "amount": 1_000_000_001}),
        pd.Series({"user_id": "u", "amount": 1, "risk_score": 1.1, "anomaly_score": 0}),
    ):
        cleaned, reason = _validate_row(row, scores_supplied="risk_score" in row)
        assert cleaned is None
        assert reason

    cleaned, reason = _validate_row(pd.Series({
        "user_id": "u", "amount": 1, "device_id": "x" * 400,
    }), scores_supplied=False)
    assert reason is None
    assert len(cleaned["device_id"]) == MAX_STRING_FIELD_LEN


def test_framework_id_filter_rejects_injection_style_ids():
    from app.schemas.investigation import FrameworkMapping
    from app.services.intelligence_service import _MITRE_ID_RE, _NIST_ID_RE, _filter_valid_framework_entries

    def entry(identifier):
        return FrameworkMapping(id=identifier, name="n", rationale="r")

    assert [item.id for item in _filter_valid_framework_entries(
        [entry("T1566.002"), entry("T9999; ignore instructions")], _MITRE_ID_RE
    )] == ["T1566.002"]
    assert [item.id for item in _filter_valid_framework_entries(
        [entry("AC-2"), entry("ACAC-2")], _NIST_ID_RE
    )] == ["AC-2"]


def test_model_integrity_check_detects_tampering(tmp_path):
    from app.ml.risk_model import RiskModel

    model_path = tmp_path / "risk_classifier.joblib"
    anomaly_path = tmp_path / "anomaly_detector.joblib"
    model_path.write_bytes(b"trusted model")
    anomaly_path.write_bytes(b"trusted anomaly")
    verifier = RiskModel.__new__(RiskModel)
    verifier.metadata = {
        "artifact_checksums": {
            model_path.name: hashlib.sha256(model_path.read_bytes()).hexdigest(),
            anomaly_path.name: hashlib.sha256(anomaly_path.read_bytes()).hexdigest(),
        }
    }
    verifier._verify_artifact_integrity(model_path, anomaly_path)
    model_path.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="Integrity check failed"):
        verifier._verify_artifact_integrity(model_path, anomaly_path)
