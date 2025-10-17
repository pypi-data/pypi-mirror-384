from enum import Enum


class IncidentPermissionSetListDataItemType(str, Enum):
    INCIDENT_PERMISSION_SETS = "incident_permission_sets"

    def __str__(self) -> str:
        return str(self.value)
