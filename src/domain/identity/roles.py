"""System role names."""

from enum import StrEnum


class SystemRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    OPERATOR = "operator"
    MAINTENANCE_ENGINEER = "maintenance_engineer"
    VIEWER = "viewer"
