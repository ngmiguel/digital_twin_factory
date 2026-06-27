"""Predictions and maintenance schema migration."""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("machine_id", sa.Uuid(), sa.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("prediction_type", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("features", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_predictions_machine_id", "predictions", ["machine_id"])
    op.create_index("ix_predictions_tenant_id", "predictions", ["tenant_id"])
    op.create_index("ix_predictions_valid_until", "predictions", ["valid_until"])

    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("machine_id", sa.Uuid(), sa.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("prediction_id", sa.Uuid(), nullable=True),
        sa.Column("assigned_to", sa.Uuid(), nullable=True),
        sa.Column("maintenance_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_maintenance_records_machine_id", "maintenance_records", ["machine_id"])
    op.create_index("ix_maintenance_records_tenant_id", "maintenance_records", ["tenant_id"])
    op.create_index(
        "ix_maintenance_records_status",
        "maintenance_records",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("maintenance_records")
    op.drop_table("predictions")
