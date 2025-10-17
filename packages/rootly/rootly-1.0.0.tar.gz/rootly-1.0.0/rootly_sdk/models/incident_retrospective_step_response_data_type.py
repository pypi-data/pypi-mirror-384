from enum import Enum


class IncidentRetrospectiveStepResponseDataType(str, Enum):
    INCIDENT_RETROSPECTIVE_STEPS = "incident_retrospective_steps"

    def __str__(self) -> str:
        return str(self.value)
