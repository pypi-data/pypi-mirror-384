from enum import Enum


class AlertEventResponseDataType(str, Enum):
    ALERT_EVENTS = "alert_events"

    def __str__(self) -> str:
        return str(self.value)
