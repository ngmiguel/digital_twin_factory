"""Machine aggregate root."""

from uuid import UUID

from src.domain.factory.enums import MachineStatus, MachineType
from src.domain.factory.events import MachineProvisioned, MachineStatusChanged
from src.domain.shared.aggregate_root import AggregateRoot
from src.domain.shared.entity import Entity
from src.domain.shared.exceptions import ValidationError


_DEFAULT_SIMULATION_CONFIG: dict[str, object] = {
    "temperature": {"base": 45.0, "noise_std": 2.0, "degradation_rate": 0.001},
    "vibration": {"base": 1.5, "noise_std": 0.3},
    "power": {"nominal_kw": 25.0, "efficiency_factor": 0.92},
    "production": {"nominal_rate": 100, "unit": "pieces/min"},
    "failure": {"mtbf_hours": 720, "mttr_hours": 4},
}


class Machine(AggregateRoot):
    tenant_id: UUID
    production_line_id: UUID
    name: str
    machine_type: MachineType
    status: MachineStatus
    simulation_config: dict[str, object]
    failure_rate: float
    nominal_production_rate: float

    @classmethod
    def provision(
        cls,
        tenant_id: UUID,
        production_line_id: UUID,
        name: str,
        machine_type: MachineType,
        failure_rate: float = 0.001,
        nominal_production_rate: float = 100.0,
        simulation_config: dict[str, object] | None = None,
    ) -> "Machine":
        if not name.strip():
            raise ValidationError("Machine name is required", field="name")
        if failure_rate < 0 or failure_rate > 1:
            raise ValidationError("Failure rate must be between 0 and 1", field="failure_rate")
        if nominal_production_rate <= 0:
            raise ValidationError("Nominal production rate must be positive", field="nominal_production_rate")

        now = Entity.now()
        machine = cls(
            id=Entity.new_id(),
            tenant_id=tenant_id,
            production_line_id=production_line_id,
            name=name.strip(),
            machine_type=machine_type,
            status=MachineStatus.OFFLINE,
            simulation_config=simulation_config or dict(_DEFAULT_SIMULATION_CONFIG),
            failure_rate=failure_rate,
            nominal_production_rate=nominal_production_rate,
            created_at=now,
            updated_at=now,
        )
        machine.add_event(
            MachineProvisioned.create(
                tenant_id=tenant_id,
                aggregate_id=machine.id,
                machine_id=machine.id,
                machine_type=machine_type.value,
                production_line_id=production_line_id,
            )
        )
        return machine

    def start(self) -> None:
        if self.status == MachineStatus.FAILURE:
            raise ValidationError("Cannot start a machine in FAILURE state", field="status")
        self._change_status(MachineStatus.RUNNING)

    def stop(self) -> None:
        self._change_status(MachineStatus.OFFLINE)

    def update(
        self,
        name: str | None = None,
        failure_rate: float | None = None,
        nominal_production_rate: float | None = None,
        simulation_config: dict[str, object] | None = None,
    ) -> None:
        if name is not None:
            if not name.strip():
                raise ValidationError("Machine name is required", field="name")
            self.name = name.strip()
        if failure_rate is not None:
            if failure_rate < 0 or failure_rate > 1:
                raise ValidationError("Failure rate must be between 0 and 1", field="failure_rate")
            self.failure_rate = failure_rate
        if nominal_production_rate is not None:
            if nominal_production_rate <= 0:
                raise ValidationError(
                    "Nominal production rate must be positive", field="nominal_production_rate"
                )
            self.nominal_production_rate = nominal_production_rate
        if simulation_config is not None:
            self.simulation_config = simulation_config
        self.updated_at = Entity.now()

    def _change_status(self, new_status: MachineStatus) -> None:
        if self.status == new_status:
            return
        old_status = self.status
        self.status = new_status
        self.updated_at = Entity.now()
        self.add_event(
            MachineStatusChanged.create(
                tenant_id=self.tenant_id,
                aggregate_id=self.id,
                machine_id=self.id,
                old_status=old_status.value,
                new_status=new_status.value,
            )
        )
