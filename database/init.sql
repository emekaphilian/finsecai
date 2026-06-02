-- FinSecAI Database Initialization
-- Creates initial schema and indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes on commonly queried fields
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_created_at ON incidents(created_at);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_risk_scores_transaction_id ON risk_scores(transaction_id);
CREATE INDEX idx_risk_scores_user_id ON risk_scores(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Optional: Create default admin user
-- (In production, use application-level user creation)
INSERT INTO users (id, username, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'admin',
  'admin@finsecai.dev',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUlNqcya', -- admin123 hashed
  'System Administrator',
  'admin',
  true,
  true,
  NOW(),
  NOW()
) ON CONFLICT (username) DO NOTHING;
