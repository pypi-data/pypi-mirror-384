from enum import Enum


class ListRetrospectiveProcessesInclude(str, Enum):
    GROUPS = "groups"
    INCIDENT_TYPES = "incident_types"
    RETROSPECTIVE_STEPS = "retrospective_steps"
    SEVERITIES = "severities"

    def __str__(self) -> str:
        return str(self.value)
