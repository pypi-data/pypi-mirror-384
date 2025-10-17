from enum import Enum


class IncidentRoleTaskListDataItemType(str, Enum):
    INCIDENT_ROLE_TASKS = "incident_role_tasks"

    def __str__(self) -> str:
        return str(self.value)
