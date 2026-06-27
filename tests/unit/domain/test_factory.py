"""Unit tests for factory domain."""

from uuid import uuid4

import pytest

from src.domain.factory.enums import MachineStatus, MachineType
from src.domain.factory.factory import Factory
from src.domain.factory.machine import Machine
from src.domain.factory.production_line import ProductionLine
from src.domain.shared.exceptions import ValidationError


def test_factory_create_emits_event() -> None:
    tenant_id = uuid4()
    factory = Factory.create(tenant_id=tenant_id, name="Usine Nord", location="Lyon")
    assert factory.name == "Usine Nord"
    assert factory.status.value == "ACTIVE"
    assert len(factory.events) == 1


def test_production_line_requires_positive_capacity() -> None:
    with pytest.raises(ValidationError):
        ProductionLine.create(
            factory_id=uuid4(),
            tenant_id=uuid4(),
            name="Line A",
            capacity=0,
        )


def test_machine_provision_defaults_to_offline() -> None:
    machine = Machine.provision(
        tenant_id=uuid4(),
        production_line_id=uuid4(),
        name="CNC-001",
        machine_type=MachineType.CNC_MILL,
    )
    assert machine.status == MachineStatus.OFFLINE
    assert len(machine.events) == 1


def test_machine_start_and_stop() -> None:
    machine = Machine.provision(
        tenant_id=uuid4(),
        production_line_id=uuid4(),
        name="CNC-001",
        machine_type=MachineType.CNC_MILL,
    )
    machine.start()
    assert machine.status == MachineStatus.RUNNING
    machine.stop()
    assert machine.status == MachineStatus.OFFLINE


def test_machine_cannot_start_when_failed() -> None:
    machine = Machine.provision(
        tenant_id=uuid4(),
        production_line_id=uuid4(),
        name="CNC-001",
        machine_type=MachineType.CNC_MILL,
    )
    machine.status = MachineStatus.FAILURE
    with pytest.raises(ValidationError):
        machine.start()
