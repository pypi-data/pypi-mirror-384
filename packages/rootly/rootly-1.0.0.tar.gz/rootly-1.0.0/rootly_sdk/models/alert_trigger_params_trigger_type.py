from enum import Enum


class AlertTriggerParamsTriggerType(str, Enum):
    ALERT = "alert"

    def __str__(self) -> str:
        return str(self.value)
