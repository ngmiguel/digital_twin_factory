"""Identity and RBAC schema migration with seed data."""

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

PERMISSIONS = [
    ("factory:read", "factory", "read", "Read factories"),
    ("factory:write", "factory", "write", "Create and update factories"),
    ("factory:delete", "factory", "delete", "Delete factories"),
    ("machine:read", "machine", "read", "Read machines"),
    ("machine:write", "machine", "write", "Create and update machines"),
    ("machine:delete", "machine", "delete", "Delete machines"),
    ("machine:start", "machine", "start", "Start machine simulation"),
    ("machine:stop", "machine", "stop", "Stop machine simulation"),
    ("metric:read", "metric", "read", "Read metrics"),
    ("metric:export", "metric", "export", "Export metrics"),
    ("alert:read", "alert", "read", "Read alerts"),
    ("alert:write", "alert", "write", "Acknowledge and resolve alerts"),
    ("prediction:read", "prediction", "read", "Read predictions"),
    ("maintenance:read", "maintenance", "read", "Read maintenance records"),
    ("maintenance:write", "maintenance", "write", "Manage maintenance records"),
    ("simulation:read", "simulation", "read", "Read simulation data"),
    ("simulation:write", "simulation", "write", "Run what-if simulations"),
    ("user:read", "user", "read", "Read users"),
    ("user:write", "user", "write", "Create and update users"),
    ("user:delete", "user", "delete", "Delete users"),
    ("role:read", "role", "read", "Read roles"),
    ("role:write", "role", "write", "Manage roles"),
    ("tenant:read", "tenant", "read", "Read tenant settings"),
    ("tenant:write", "tenant", "write", "Manage tenant settings"),
    ("notification:read", "notification", "read", "Read notifications"),
    ("notification:write", "notification", "write", "Manage notifications"),
]

ROLE_PERMISSIONS = {
    "super_admin": [p[0] for p in PERMISSIONS],
    "tenant_admin": [
        "factory:read", "factory:write", "factory:delete",
        "machine:read", "machine:write", "machine:delete", "machine:start", "machine:stop",
        "metric:read", "metric:export",
        "alert:read", "alert:write",
        "prediction:read",
        "maintenance:read", "maintenance:write",
        "simulation:read", "simulation:write",
        "user:read", "user:write", "user:delete",
        "role:read",
        "tenant:read",
        "notification:read", "notification:write",
    ],
    "operator": [
        "factory:read", "machine:read", "metric:read",
        "alert:read", "alert:write", "notification:read",
    ],
    "maintenance_engineer": [
        "factory:read", "machine:read", "metric:read", "metric:export",
        "alert:read", "alert:write", "prediction:read",
        "maintenance:read", "maintenance:write",
        "simulation:write", "notification:read",
    ],
    "viewer": [
        "factory:read", "machine:read", "metric:read", "alert:read",
    ],
}

ROLES = [
    ("super_admin", "Platform super administrator", True),
    ("tenant_admin", "Tenant administrator", True),
    ("operator", "Factory operator", True),
    ("maintenance_engineer", "Maintenance engineer", True),
    ("viewer", "Read-only viewer", True),
]


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("settings", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_permissions_name", "permissions", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "permission_id",
            sa.Uuid(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    now = datetime.now(UTC)
    permission_ids: dict[str, uuid.UUID] = {}
    role_ids: dict[str, uuid.UUID] = {}

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
        sa.column("description", sa.Text()),
    )
    permission_rows = []
    for name, resource, action, description in PERMISSIONS:
        permission_id = uuid.uuid4()
        permission_ids[name] = permission_id
        permission_rows.append(
            {
                "id": permission_id,
                "name": name,
                "resource": resource,
                "action": action,
                "description": description,
            }
        )
    op.bulk_insert(permissions_table, permission_rows)

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_system", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    role_rows = []
    for name, description, is_system in ROLES:
        role_id = uuid.uuid4()
        role_ids[name] = role_id
        role_rows.append(
            {
                "id": role_id,
                "name": name,
                "description": description,
                "is_system": is_system,
                "created_at": now,
            }
        )
    op.bulk_insert(roles_table, role_rows)

    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )
    rp_rows = []
    for role_name, perm_names in ROLE_PERMISSIONS.items():
        for perm_name in perm_names:
            rp_rows.append(
                {"role_id": role_ids[role_name], "permission_id": permission_ids[perm_name]}
            )
    op.bulk_insert(role_permissions_table, rp_rows)


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("tenants")
