"""add ml_prediction_audit table

This is a template for Alembic once scaffolding exists.
"""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "ml_prediction_audit",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey(
            "tenants.id"), nullable=False),
        sa.Column("incident_id", sa.String(), sa.ForeignKey(
            "incidents.id"), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("feature_values", sa.JSON(), nullable=False),
        sa.Column("feature_contributions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_ml_prediction_audit_tenant_id",
                    "ml_prediction_audit", ["tenant_id"])
    op.create_index("ix_ml_prediction_audit_incident_id",
                    "ml_prediction_audit", ["incident_id"])
    op.create_index("ix_ml_prediction_audit_model_version",
                    "ml_prediction_audit", ["model_version"])
    op.create_index("ix_ml_prediction_audit_created_at",
                    "ml_prediction_audit", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ml_prediction_audit_created_at",
                  table_name="ml_prediction_audit")
    op.drop_index("ix_ml_prediction_audit_model_version",
                  table_name="ml_prediction_audit")
    op.drop_index("ix_ml_prediction_audit_incident_id",
                  table_name="ml_prediction_audit")
    op.drop_index("ix_ml_prediction_audit_tenant_id",
                  table_name="ml_prediction_audit")
    op.drop_table("ml_prediction_audit")
