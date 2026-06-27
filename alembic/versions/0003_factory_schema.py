"""Factory schema migration."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "factories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("config", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_factories_tenant_id", "factories", ["tenant_id"])

    op.create_table(
        "production_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("factory_id", sa.Uuid(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_production_lines_factory_id", "production_lines", ["factory_id"])
    op.create_index("ix_production_lines_tenant_id", "production_lines", ["tenant_id"])

    op.create_table(
        "machines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "production_line_id",
            sa.Uuid(),
            sa.ForeignKey("production_lines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("machine_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="OFFLINE"),
        sa.Column("simulation_config", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("failure_rate", sa.Float(), nullable=False, server_default="0.001"),
        sa.Column("nominal_production_rate", sa.Float(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_machines_production_line_id", "machines", ["production_line_id"])
    op.create_index("ix_machines_tenant_id", "machines", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("machines")
    op.drop_table("production_lines")
    op.drop_table("factories")
