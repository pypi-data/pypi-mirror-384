from enum import Enum


class UpdateIncidentTaskParamsTaskType(str, Enum):
    UPDATE_INCIDENT = "update_incident"

    def __str__(self) -> str:
        return str(self.value)
