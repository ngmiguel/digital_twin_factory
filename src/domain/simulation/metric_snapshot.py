"""Simulation metric snapshot value object."""

from src.domain.factory.enums import MachineStatus
from src.domain.shared.value_object import ValueObject


class MetricSnapshot(ValueObject):
    temperature: float
    vibration: float
    power_consumption: float
    production_rate: float
    machine_status: MachineStatus
