from enum import Enum


class UpdateIncidentEventServiceDataType(str, Enum):
    INCIDENT_EVENT_SERVICES = "incident_event_services"

    def __str__(self) -> str:
        return str(self.value)
