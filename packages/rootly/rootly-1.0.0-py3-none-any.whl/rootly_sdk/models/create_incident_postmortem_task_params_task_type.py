from enum import Enum


class CreateIncidentPostmortemTaskParamsTaskType(str, Enum):
    CREATE_INCIDENT_POSTMORTEM = "create_incident_postmortem"

    def __str__(self) -> str:
        return str(self.value)
