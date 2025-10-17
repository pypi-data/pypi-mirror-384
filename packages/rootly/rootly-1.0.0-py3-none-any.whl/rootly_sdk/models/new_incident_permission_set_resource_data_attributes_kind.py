from enum import Enum


class NewIncidentPermissionSetResourceDataAttributesKind(str, Enum):
    INCIDENT_TYPES = "incident_types"
    SEVERITIES = "severities"
    STATUSES = "statuses"
    SUB_STATUSES = "sub_statuses"

    def __str__(self) -> str:
        return str(self.value)
