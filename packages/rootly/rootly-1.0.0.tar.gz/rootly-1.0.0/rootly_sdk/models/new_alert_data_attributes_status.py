from enum import Enum


class NewAlertDataAttributesStatus(str, Enum):
    OPEN = "open"
    TRIGGERED = "triggered"

    def __str__(self) -> str:
        return str(self.value)
