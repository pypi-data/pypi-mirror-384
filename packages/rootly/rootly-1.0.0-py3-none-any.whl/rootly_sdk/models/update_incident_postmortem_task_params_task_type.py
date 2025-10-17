from enum import Enum


class UpdateIncidentPostmortemTaskParamsTaskType(str, Enum):
    UPDATE_INCIDENT_POSTMORTEM = "update_incident_postmortem"

    def __str__(self) -> str:
        return str(self.value)
