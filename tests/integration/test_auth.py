"""Integration tests for authentication — requires PostgreSQL and Redis."""

import pytest

pytestmark = pytest.mark.skip(reason="Requires PostgreSQL and Redis — run with: pytest -m integration")
