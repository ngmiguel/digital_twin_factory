"""Pure simulation engine — generates industrial machine metrics."""

import random
from dataclasses import dataclass

from src.domain.factory.enums import MachineStatus, MachineType
from src.domain.factory.machine import Machine
from src.domain.simulation.metric_snapshot import MetricSnapshot
from src.domain.simulation.simulation_state import SimulationState


@dataclass(frozen=True)
class TickResult:
    metrics: MetricSnapshot
    state: SimulationState
    new_status: MachineStatus | None = None


class VirtualMachineEngine:
    """Generates realistic metric streams for virtual industrial machines."""

    def tick(self, machine: Machine, state: SimulationState) -> TickResult:
        config = machine.simulation_config
        temp_cfg = config.get("temperature", {})
        vib_cfg = config.get("vibration", {})
        power_cfg = config.get("power", {})
        failure_cfg = config.get("failure", {})

        tick_count = state.tick_count + 1
        elapsed = state.elapsed_seconds + 1.0
        degradation_rate = float(temp_cfg.get("degradation_rate", 0.001))
        degradation = max(0.5, 1.0 - (tick_count * degradation_rate))

        temp_base = float(temp_cfg.get("base", 45.0))
        temp_noise = float(temp_cfg.get("noise_std", 2.0))
        temperature = temp_base * (1 + (1 - degradation) * 0.3) + random.gauss(0, temp_noise)
        temperature = max(0.0, temperature)

        vib_base = float(vib_cfg.get("base", 1.5))
        vib_noise = float(vib_cfg.get("noise_std", 0.3))
        vibration = vib_base * (1 + (1 - degradation) * 0.5) + random.gauss(0, vib_noise)
        vibration = max(0.0, vibration)

        nominal_kw = float(power_cfg.get("nominal_kw", 25.0))
        efficiency = float(power_cfg.get("efficiency_factor", 0.92))
        production_rate = machine.nominal_production_rate * degradation
        power_consumption = nominal_kw * (production_rate / machine.nominal_production_rate) * efficiency

        type_factor = _machine_type_factor(machine.machine_type)
        temperature *= type_factor
        vibration *= type_factor

        new_status: MachineStatus | None = None
        current_status = machine.status

        if _should_fail(machine.failure_rate, failure_cfg, tick_count):
            current_status = MachineStatus.FAILURE
            new_status = MachineStatus.FAILURE
            production_rate = 0.0
            power_consumption = nominal_kw * 0.1
        elif degradation < 0.85 and machine.status == MachineStatus.RUNNING:
            current_status = MachineStatus.DEGRADED
            new_status = MachineStatus.DEGRADED

        metrics = MetricSnapshot(
            temperature=round(temperature, 2),
            vibration=round(vibration, 3),
            power_consumption=round(power_consumption, 2),
            production_rate=round(production_rate, 2),
            machine_status=current_status,
        )

        new_state = SimulationState(
            tick_count=tick_count,
            degradation_factor=degradation,
            elapsed_seconds=elapsed,
        )

        return TickResult(metrics=metrics, state=new_state, new_status=new_status)


def _machine_type_factor(machine_type: MachineType) -> float:
    factors = {
        MachineType.CNC_MILL: 1.1,
        MachineType.ROBOT_ARM: 1.0,
        MachineType.CONVEYOR: 0.8,
        MachineType.PRESS: 1.3,
        MachineType.WELDER: 1.2,
        MachineType.PACKAGING: 0.9,
    }
    return factors.get(machine_type, 1.0)


def _should_fail(
    failure_rate: float,
    failure_cfg: dict[str, object],
    tick_count: int,
) -> bool:
    mtbf_hours = float(failure_cfg.get("mtbf_hours", 720))
    ticks_per_hour = 3600
    probability = failure_rate + (tick_count / (mtbf_hours * ticks_per_hour))
    return random.random() < min(probability, 0.05)
