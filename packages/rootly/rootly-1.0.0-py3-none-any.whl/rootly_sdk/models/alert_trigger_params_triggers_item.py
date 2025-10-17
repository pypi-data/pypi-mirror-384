from enum import Enum


class AlertTriggerParamsTriggersItem(str, Enum):
    ALERT_CREATED = "alert_created"
    ALERT_STATUS_UPDATED = "alert_status_updated"

    def __str__(self) -> str:
        return str(self.value)
