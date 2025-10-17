from enum import Enum


class AlertUrgencyListDataItemType(str, Enum):
    ALERT_URGENCIES = "alert_urgencies"

    def __str__(self) -> str:
        return str(self.value)
