-- Apply to existing production databases before deploying Tier 4.
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS str_filed_at TIMESTAMP NULL;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS str_reference VARCHAR NULL;
