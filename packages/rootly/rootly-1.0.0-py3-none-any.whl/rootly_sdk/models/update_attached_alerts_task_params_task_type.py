from enum import Enum


class UpdateAttachedAlertsTaskParamsTaskType(str, Enum):
    UPDATE_ATTACHED_ALERTS = "update_attached_alerts"

    def __str__(self) -> str:
        return str(self.value)
