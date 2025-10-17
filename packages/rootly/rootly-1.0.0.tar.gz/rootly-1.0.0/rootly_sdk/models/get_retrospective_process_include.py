from enum import Enum


class GetRetrospectiveProcessInclude(str, Enum):
    GROUPS = "groups"
    INCIDENT_TYPES = "incident_types"
    RETROSPECTIVE_STEPS = "retrospective_steps"
    SEVERITIES = "severities"

    def __str__(self) -> str:
        return str(self.value)
