"""Unit tests for virtual machine simulation engine."""

from uuid import uuid4

from src.domain.factory.enums import MachineStatus, MachineType
from src.domain.factory.machine import Machine
from src.domain.simulation.simulation_state import SimulationState
from src.domain.simulation.virtual_machine_engine import VirtualMachineEngine


def _make_machine() -> Machine:
    return Machine.provision(
        tenant_id=uuid4(),
        production_line_id=uuid4(),
        name="CNC-001",
        machine_type=MachineType.CNC_MILL,
        nominal_production_rate=100.0,
    )


def test_tick_generates_non_negative_metrics() -> None:
    engine = VirtualMachineEngine()
    machine = _make_machine()
    machine.status = MachineStatus.RUNNING
    state = SimulationState()

    for _ in range(50):
        result = engine.tick(machine, state)
        assert result.metrics.temperature >= 0
        assert result.metrics.vibration >= 0
        assert result.metrics.power_consumption >= 0
        assert result.metrics.production_rate >= 0
        state = result.state


def test_tick_increments_state() -> None:
    engine = VirtualMachineEngine()
    machine = _make_machine()
    machine.status = MachineStatus.RUNNING

    result = engine.tick(machine, SimulationState())
    assert result.state.tick_count == 1
    assert result.state.elapsed_seconds == 1.0
