from enum import Enum


class UpdateAttachedAlertsTaskParamsStatus(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

    def __str__(self) -> str:
        return str(self.value)
