from enum import Enum


class AlertEventKind(str, Enum):
    ACTION = "action"
    ALERT_GROUPING = "alert_grouping"
    ALERT_ROUTING = "alert_routing"
    ALERT_URGENCY = "alert_urgency"
    INFORMATIONAL = "informational"
    MAINTENANCE = "maintenance"
    NOISE = "noise"
    NOTE = "note"
    NOTIFICATION = "notification"
    RECORDING = "recording"
    STATUS_UPDATE = "status_update"

    def __str__(self) -> str:
        return str(self.value)
