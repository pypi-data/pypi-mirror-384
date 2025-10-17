from enum import Enum


class UpdateVictorOpsIncidentTaskParamsTaskType(str, Enum):
    UPDATE_VICTOR_OPS_INCIDENT = "update_victor_ops_incident"

    def __str__(self) -> str:
        return str(self.value)
