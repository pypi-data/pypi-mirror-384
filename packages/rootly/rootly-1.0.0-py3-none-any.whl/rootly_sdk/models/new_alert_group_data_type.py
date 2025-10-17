from enum import Enum


class NewAlertGroupDataType(str, Enum):
    ALERT_GROUPS = "alert_groups"

    def __str__(self) -> str:
        return str(self.value)
