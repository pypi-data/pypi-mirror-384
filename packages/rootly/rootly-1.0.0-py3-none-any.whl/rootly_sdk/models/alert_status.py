from enum import Enum


class AlertStatus(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    OPEN = "open"
    RESOLVED = "resolved"
    TRIGGERED = "triggered"

    def __str__(self) -> str:
        return str(self.value)
