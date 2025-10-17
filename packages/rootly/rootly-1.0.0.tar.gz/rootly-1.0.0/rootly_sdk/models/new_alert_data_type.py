from enum import Enum


class NewAlertDataType(str, Enum):
    ALERTS = "alerts"

    def __str__(self) -> str:
        return str(self.value)
