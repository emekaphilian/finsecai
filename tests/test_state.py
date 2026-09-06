from src.agents.state import AgentState


def test_state_schema():
    state: AgentState = {
        "incident": {},
        "fraud_signals": [],
        "fraud_score": 0.0,
        "fraud_verdict": "clean",
        "risk_factors": [],
        "risk_score": 0.0,
        "risk_level": "low",
        "compliance_flags": [],
        "compliance_score": 1.0,
        "regulations_triggered": [],
        "summary": "",
        "recommended_action": "",
        "confidence": 0.0,
        "errors": [],
        "analysis_status": "failed",
    }

    assert state["fraud_score"] == 0.0
