-- Production Database Initialization for FinSecAI
-- PostgreSQL 13+
-- Includes versioning, auditing, and performance optimization

-- ===== CREATE SCHEMA =====
CREATE SCHEMA IF NOT EXISTS finsecai;
CREATE SCHEMA IF NOT EXISTS audit;

-- ===== AUDIT TRIGGER FUNCTION =====
CREATE OR REPLACE FUNCTION audit.audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data TEXT;
    v_new_data TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_old_data := to_json(OLD);
        v_new_data := NULL;
    ELSIF TG_OP = 'INSERT' THEN
        v_old_data := NULL;
        v_new_data := to_json(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        v_old_data := to_json(OLD);
        v_new_data := to_json(NEW);
    END IF;
    
    INSERT INTO audit.audit_log (
        operation, schema_name, table_name, record_id,
        old_data, new_data, changed_by, changed_at
    ) VALUES (
        TG_OP, TG_TABLE_SCHEMA, TG_TABLE_NAME, 
        COALESCE(NEW.id, OLD.id),
        v_old_data, v_new_data,
        CURRENT_USER, NOW()
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===== AUDIT LOG TABLE =====
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id BIGSERIAL PRIMARY KEY,
    operation VARCHAR(6) NOT NULL,
    schema_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    record_id TEXT,
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (changed_at);

-- Create monthly partitions
CREATE TABLE audit.audit_log_2026_01 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE audit.audit_log_2026_02 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE audit.audit_log_2026_03 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE audit.audit_log_2026_04 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE INDEX idx_audit_log_table ON audit.audit_log(table_name, changed_at DESC);
CREATE INDEX idx_audit_log_user ON audit.audit_log(changed_by, changed_at DESC);
CREATE INDEX idx_audit_log_record ON audit.audit_log(record_id);

-- ===== MAIN TABLES =====

-- Incidents
CREATE TABLE IF NOT EXISTS finsecai.incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id VARCHAR(255) UNIQUE NOT NULL,
    tenant_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    amount DECIMAL(15, 2),
    incident_type VARCHAR(100),
    severity VARCHAR(50),
    status VARCHAR(50) DEFAULT 'NEW',
    risk_score DECIMAL(3, 2),
    analysis_results JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
) PARTITION BY RANGE (timestamp);

-- Create monthly incident partitions
CREATE TABLE finsecai.incidents_2026_01 PARTITION OF finsecai.incidents
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE finsecai.incidents_2026_02 PARTITION OF finsecai.incidents
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE finsecai.incidents_2026_03 PARTITION OF finsecai.incidents
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE finsecai.incidents_2026_04 PARTITION OF finsecai.incidents
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE INDEX idx_incidents_tenant ON finsecai.incidents(tenant_id, timestamp DESC);
CREATE INDEX idx_incidents_user ON finsecai.incidents(user_id, timestamp DESC);
CREATE INDEX idx_incidents_status ON finsecai.incidents(status, created_at DESC);
CREATE INDEX idx_incidents_severity ON finsecai.incidents(severity);
CREATE INDEX idx_incidents_incident_id ON finsecai.incidents(incident_id);

-- Tenants
CREATE TABLE IF NOT EXISTS finsecai.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    config JSONB DEFAULT '{}',
    max_users INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_tenants_active ON finsecai.tenants(is_active);
CREATE INDEX idx_tenants_name ON finsecai.tenants(name);

-- Users
CREATE TABLE IF NOT EXISTS finsecai.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES finsecai.tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'analyst',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, email),
    UNIQUE(tenant_id, username)
);

CREATE INDEX idx_users_tenant ON finsecai.users(tenant_id, is_active);
CREATE INDEX idx_users_email ON finsecai.users(email);

-- Analysis Results
CREATE TABLE IF NOT EXISTS finsecai.analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES finsecai.incidents(id) ON DELETE CASCADE,
    analyst_id UUID NOT NULL REFERENCES finsecai.users(id) ON DELETE SET NULL,
    analysis_type VARCHAR(100),
    result JSONB NOT NULL,
    confidence_score DECIMAL(3, 2),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analysis_incident ON finsecai.analysis_results(incident_id);
CREATE INDEX idx_analysis_type ON finsecai.analysis_results(analysis_type, created_at DESC);

-- API Logs
CREATE TABLE IF NOT EXISTS finsecai.api_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    user_id VARCHAR(255),
    tenant_id UUID,
    status_code INTEGER,
    response_time_ms DECIMAL(10, 2),
    request_size INTEGER,
    response_size INTEGER,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE finsecai.api_logs_2026_01 PARTITION OF finsecai.api_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_api_logs_endpoint ON finsecai.api_logs(endpoint, created_at DESC);
CREATE INDEX idx_api_logs_status ON finsecai.api_logs(status_code, created_at DESC);
CREATE INDEX idx_api_logs_user ON finsecai.api_logs(user_id, created_at DESC);

-- Performance Metrics
CREATE TABLE IF NOT EXISTS finsecai.performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    component VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15, 4) NOT NULL,
    unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE finsecai.performance_metrics_2026_01 PARTITION OF finsecai.performance_metrics
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_metrics_component ON finsecai.performance_metrics(component, created_at DESC);
CREATE INDEX idx_metrics_metric ON finsecai.performance_metrics(metric_name, created_at DESC);

-- ===== ADD AUDIT TRIGGERS =====
CREATE TRIGGER audit_incidents AFTER INSERT OR UPDATE OR DELETE ON finsecai.incidents
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON finsecai.users
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

CREATE TRIGGER audit_analysis AFTER INSERT OR UPDATE OR DELETE ON finsecai.analysis_results
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

-- ===== GRANT PERMISSIONS =====
GRANT USAGE ON SCHEMA finsecai TO finsecai_user;
GRANT USAGE ON SCHEMA audit TO finsecai_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA finsecai TO finsecai_user;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO finsecai_user;

-- ===== VACUUM & ANALYZE =====
VACUUM ANALYZE;

-- ===== INITIAL DATA =====
INSERT INTO finsecai.tenants (name, description)
VALUES ('Default Tenant', 'Default tenant for testing') ON CONFLICT DO NOTHING;

COMMIT;
