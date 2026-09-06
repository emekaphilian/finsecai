CREATE TABLE IF NOT EXISTS ml_prediction_audit (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
    incident_id VARCHAR NOT NULL REFERENCES incidents(id),
    model_version VARCHAR NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    feature_values JSON NOT NULL,
    feature_contributions JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ml_prediction_audit_tenant_id ON ml_prediction_audit (tenant_id);
CREATE INDEX IF NOT EXISTS ix_ml_prediction_audit_incident_id ON ml_prediction_audit (incident_id);
CREATE INDEX IF NOT EXISTS ix_ml_prediction_audit_model_version ON ml_prediction_audit (model_version);
CREATE INDEX IF NOT EXISTS ix_ml_prediction_audit_created_at ON ml_prediction_audit (created_at);
