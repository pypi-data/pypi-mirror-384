from enum import Enum


class AlertListDataItemType(str, Enum):
    ALERTS = "alerts"

    def __str__(self) -> str:
        return str(self.value)
