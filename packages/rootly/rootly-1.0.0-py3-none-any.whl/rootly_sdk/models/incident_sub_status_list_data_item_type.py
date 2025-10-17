from enum import Enum


class IncidentSubStatusListDataItemType(str, Enum):
    INCIDENT_SUB_STATUSES = "incident_sub_statuses"

    def __str__(self) -> str:
        return str(self.value)
