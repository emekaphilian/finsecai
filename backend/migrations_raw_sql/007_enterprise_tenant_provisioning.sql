-- Phase 2 enterprise tenant foundation.
-- Review and apply through the deployment migration process; this file is not
-- executed by application startup and performs no data deletion.

-- Existing rows are intentionally left without a business type until their
-- provenance has been reviewed. New application provisioning supplies both.
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tenant_type VARCHAR NULL;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS provenance VARCHAR NOT NULL DEFAULT 'UNKNOWN';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS industry VARCHAR NOT NULL DEFAULT '';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS website VARCHAR NOT NULL DEFAULT '';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS contact_email VARCHAR NOT NULL DEFAULT '';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS contact_phone VARCHAR NOT NULL DEFAULT '';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS country VARCHAR NOT NULL DEFAULT '';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS timezone VARCHAR NOT NULL DEFAULT 'UTC';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE users ALTER COLUMN tenant_id DROP NOT NULL;

ALTER TABLE audit_events ALTER COLUMN tenant_id DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_tenants_tenant_type'
    ) THEN
        ALTER TABLE tenants ADD CONSTRAINT ck_tenants_tenant_type
            CHECK (tenant_type IS NULL OR tenant_type IN ('DEMO', 'CUSTOMER'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_tenants_provenance'
    ) THEN
        ALTER TABLE tenants ADD CONSTRAINT ck_tenants_provenance
            CHECK (provenance IN (
                'LEGITIMATE_DEMO', 'LEGITIMATE_CUSTOMER', 'BENCHMARK',
                'DIAGNOSTIC', 'TEST', 'UNKNOWN'
            ));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_tenants_status'
    ) THEN
        ALTER TABLE tenants ADD CONSTRAINT ck_tenants_status
            CHECK (status IN ('ACTIVE', 'SUSPENDED', 'INACTIVE'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_status'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT ck_users_status
            CHECK (status IN ('ACTIVE', 'DISABLED'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS tenant_configurations (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL UNIQUE REFERENCES tenants(id),
    configuration JSON NOT NULL DEFAULT '{}'::json,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_tenant_configurations_tenant_id
    ON tenant_configurations (tenant_id);

-- Existing Acme remains the only known demo marker; no other tenant is
-- reclassified or deleted by this migration.
UPDATE tenants
SET tenant_type = 'DEMO', provenance = 'LEGITIMATE_DEMO'
WHERE lower(name) = 'acme corp';

UPDATE tenants
SET provenance = 'BENCHMARK'
WHERE lower(description) LIKE '%benchmark%';

UPDATE tenants
SET provenance = 'DIAGNOSTIC'
WHERE lower(name) LIKE '%diagnostic%'
    OR lower(name) LIKE 'diag-%';
