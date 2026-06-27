"""Factory bounded context enums."""

from enum import StrEnum


class FactoryStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class ProductionLineStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class MachineType(StrEnum):
    CNC_MILL = "CNC_MILL"
    ROBOT_ARM = "ROBOT_ARM"
    CONVEYOR = "CONVEYOR"
    PRESS = "PRESS"
    WELDER = "WELDER"
    PACKAGING = "PACKAGING"


class MachineStatus(StrEnum):
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    DEGRADED = "DEGRADED"
    FAILURE = "FAILURE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
