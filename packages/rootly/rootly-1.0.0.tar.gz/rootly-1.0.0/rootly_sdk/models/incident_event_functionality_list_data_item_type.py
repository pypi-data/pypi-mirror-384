from enum import Enum


class IncidentEventFunctionalityListDataItemType(str, Enum):
    INCIDENT_EVENT_FUNCTIONALITIES = "incident_event_functionalities"

    def __str__(self) -> str:
        return str(self.value)
