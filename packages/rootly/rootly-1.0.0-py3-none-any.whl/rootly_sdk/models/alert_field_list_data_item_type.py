from enum import Enum


class AlertFieldListDataItemType(str, Enum):
    ALERT_FIELDS = "alert_fields"

    def __str__(self) -> str:
        return str(self.value)
