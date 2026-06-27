"""Virtual machine simulation state."""

from src.domain.shared.value_object import ValueObject


class SimulationState(ValueObject):
    tick_count: int = 0
    degradation_factor: float = 1.0
    elapsed_seconds: float = 0.0
