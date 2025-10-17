from enum import Enum


class CreateIncidentTaskParamsTaskType(str, Enum):
    CREATE_INCIDENT = "create_incident"

    def __str__(self) -> str:
        return str(self.value)
