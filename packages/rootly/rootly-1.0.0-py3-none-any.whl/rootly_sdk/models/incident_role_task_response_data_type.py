from enum import Enum


class IncidentRoleTaskResponseDataType(str, Enum):
    INCIDENT_ROLE_TASKS = "incident_role_tasks"

    def __str__(self) -> str:
        return str(self.value)
