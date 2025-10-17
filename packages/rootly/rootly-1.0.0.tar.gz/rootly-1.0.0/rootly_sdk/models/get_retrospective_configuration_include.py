from enum import Enum


class GetRetrospectiveConfigurationInclude(str, Enum):
    GROUPS = "groups"
    INCIDENT_TYPES = "incident_types"
    SEVERITIES = "severities"

    def __str__(self) -> str:
        return str(self.value)
