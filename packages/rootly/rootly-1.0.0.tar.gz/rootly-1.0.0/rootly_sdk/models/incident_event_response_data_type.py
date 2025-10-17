from enum import Enum


class IncidentEventResponseDataType(str, Enum):
    INCIDENT_EVENTS = "incident_events"

    def __str__(self) -> str:
        return str(self.value)
