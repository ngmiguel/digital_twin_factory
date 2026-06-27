"""Identity value objects."""

import re

from src.domain.shared.exceptions import ValidationError
from src.domain.shared.value_object import ValueObject

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Email(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> "Email":
        normalized = value.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            raise ValidationError("Invalid email address", field="email")
        return cls(value=normalized)


class TenantSlug(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> "TenantSlug":
        normalized = value.strip().lower()
        if not _SLUG_PATTERN.match(normalized) or len(normalized) < 3:
            raise ValidationError(
                "Slug must be at least 3 characters (lowercase, numbers, hyphens)",
                field="slug",
            )
        return cls(value=normalized)

    @classmethod
    def from_name(cls, name: str) -> "TenantSlug":
        slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
        if len(slug) < 3:
            slug = f"{slug}-org" if slug else "org"
        return cls.create(slug[:50])
