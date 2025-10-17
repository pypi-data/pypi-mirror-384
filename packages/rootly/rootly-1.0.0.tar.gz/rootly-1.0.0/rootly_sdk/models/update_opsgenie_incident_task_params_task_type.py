from enum import Enum


class UpdateOpsgenieIncidentTaskParamsTaskType(str, Enum):
    UPDATE_OPSGENIE_INCIDENT = "update_opsgenie_incident"

    def __str__(self) -> str:
        return str(self.value)
