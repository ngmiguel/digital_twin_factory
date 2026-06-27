"""Permission matching utilities."""

from fnmatch import fnmatch


def has_permission(user_permissions: list[str], required: str) -> bool:
    """Check if user has required permission, supporting wildcards."""
    if "*" in user_permissions:
        return True

    if required in user_permissions:
        return True

    resource, _, action = required.partition(":")
    wildcard = f"{resource}:*"
    if wildcard in user_permissions:
        return True

    return any(fnmatch(required, pattern) for pattern in user_permissions if "*" in pattern)
