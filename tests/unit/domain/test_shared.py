"""Unit tests for domain shared primitives."""

from uuid import uuid4

import pytest

from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.domain_event import DomainEvent
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import EntityNotFoundError, ValidationError


class SampleEvent(DomainEvent):
    message: str = "test"


class SampleEntity(Entity):
    name: str


class SampleAggregate(AggregateRoot):
    name: str


def test_entity_creation() -> None:
    entity_id = uuid4()
    now = Entity.now()
    entity = SampleEntity(id=entity_id, created_at=now, updated_at=now, name="test")
    assert entity.id == entity_id
    assert entity.name == "test"


def test_aggregate_root_collects_events() -> None:
    entity_id = uuid4()
    now = Entity.now()
    aggregate = SampleAggregate(id=entity_id, created_at=now, updated_at=now, name="factory")
    event = SampleEvent.create(aggregate_id=entity_id, message="created")
    aggregate.add_event(event)
    assert len(aggregate.events) == 1
    aggregate.clear_events()
    assert len(aggregate.events) == 0


def test_entity_not_found_error() -> None:
    entity_id = uuid4()
    error = EntityNotFoundError("Factory", entity_id)
    assert error.code == "NOT_FOUND"
    assert str(entity_id) in error.message


def test_validation_error_with_field() -> None:
    error = ValidationError("Invalid value", field="email")
    assert error.code == "VALIDATION_ERROR"
    assert error.field == "email"
