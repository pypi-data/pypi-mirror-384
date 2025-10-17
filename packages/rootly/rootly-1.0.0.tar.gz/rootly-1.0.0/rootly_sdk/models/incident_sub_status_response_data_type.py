from enum import Enum


class IncidentSubStatusResponseDataType(str, Enum):
    INCIDENT_SUB_STATUSES = "incident_sub_statuses"

    def __str__(self) -> str:
        return str(self.value)
