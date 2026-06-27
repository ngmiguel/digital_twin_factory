"""Unit tests for identity domain."""

import pytest

from src.domain.identity.tenant import Tenant
from src.domain.identity.value_objects import Email, TenantSlug
from src.domain.shared.exceptions import ValidationError


def test_email_normalization() -> None:
    email = Email.create("  Admin@Factory.COM  ")
    assert email.value == "admin@factory.com"


def test_email_invalid_raises() -> None:
    with pytest.raises(ValidationError):
        Email.create("not-an-email")


def test_tenant_slug_from_name() -> None:
    slug = TenantSlug.from_name("Usine Dupont & Fils")
    assert slug.value == "usine-dupont-fils"


def test_tenant_create_emits_event() -> None:
    tenant = Tenant.create("Usine Nord")
    assert tenant.slug == "usine-nord"
    assert len(tenant.events) == 1
    assert tenant.events[0].name == "Usine Nord"
