-- Preserve source-system fields for flexible uploads on existing databases.
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS raw_payload JSON;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS normalization_metadata JSON;
