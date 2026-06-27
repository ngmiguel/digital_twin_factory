"""Machine metrics schema migration."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "machine_metrics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("machine_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("vibration", sa.Float(), nullable=False),
        sa.Column("power_consumption", sa.Float(), nullable=False),
        sa.Column("production_rate", sa.Float(), nullable=False),
        sa.Column("machine_status", sa.String(50), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_machine_metrics_machine_id", "machine_metrics", ["machine_id"])
    op.create_index("ix_machine_metrics_tenant_id", "machine_metrics", ["tenant_id"])
    op.create_index(
        "ix_machine_metrics_machine_recorded",
        "machine_metrics",
        ["machine_id", "recorded_at"],
    )


def downgrade() -> None:
    op.drop_table("machine_metrics")
