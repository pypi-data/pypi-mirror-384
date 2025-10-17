from enum import Enum


class UpdateAlertGroupDataType(str, Enum):
    ALERT_GROUPS = "alert_groups"

    def __str__(self) -> str:
        return str(self.value)
