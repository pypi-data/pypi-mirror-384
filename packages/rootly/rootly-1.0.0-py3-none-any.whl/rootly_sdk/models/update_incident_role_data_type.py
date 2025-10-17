from enum import Enum


class UpdateIncidentRoleDataType(str, Enum):
    INCIDENT_ROLES = "incident_roles"

    def __str__(self) -> str:
        return str(self.value)
