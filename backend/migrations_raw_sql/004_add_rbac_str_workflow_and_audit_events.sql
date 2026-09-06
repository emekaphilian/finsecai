-- Tier 4 RBAC workflow migration. Existing users keep their current role;
-- only unrecognized legacy roles are reduced to the least-privilege analyst role.
UPDATE users
SET role = 'analyst'
WHERE lower(role) NOT IN ('admin', 'compliance_officer', 'analyst', 'viewer');

CREATE TABLE IF NOT EXISTS suspicious_transaction_reports (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
    incident_id VARCHAR NOT NULL REFERENCES incidents(id),
    narrative TEXT NOT NULL DEFAULT '',
    status VARCHAR NOT NULL DEFAULT 'draft',
    created_by_user_id VARCHAR NOT NULL REFERENCES users(id),
    submitted_at TIMESTAMP NULL,
    submission_reference VARCHAR NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_suspicious_transaction_reports_tenant_id
    ON suspicious_transaction_reports (tenant_id);
CREATE INDEX IF NOT EXISTS ix_suspicious_transaction_reports_incident_id
    ON suspicious_transaction_reports (incident_id);

CREATE TABLE IF NOT EXISTS audit_events (
    id VARCHAR PRIMARY KEY,
    actor_user_id VARCHAR NOT NULL REFERENCES users(id),
    tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
    action VARCHAR NOT NULL,
    resource_type VARCHAR NOT NULL,
    resource_id VARCHAR NOT NULL,
    result VARCHAR NOT NULL DEFAULT 'success',
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_audit_events_actor_user_id ON audit_events (actor_user_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_tenant_id ON audit_events (tenant_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_action ON audit_events (action);
