from enum import Enum


class UpdateAlertDataType(str, Enum):
    ALERTS = "alerts"

    def __str__(self) -> str:
        return str(self.value)
