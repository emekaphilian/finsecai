from src.orchestration.run_graph import run_full_pipeline


def test_pipeline_execution():
    incident = {
        "incident_id": "TEST-001",
        "user_id": "user_123",
        "amount": 15000,
        "country_code": "NG",
        "kyc_verified": True
    }

    result = run_full_pipeline(incident)

    assert "fraud" in result
    assert "risk" in result
    assert "compliance" in result
    assert "intelligence" in result
