from enum import Enum


class IncidentTriggerParamsTriggerType(str, Enum):
    INCIDENT = "incident"

    def __str__(self) -> str:
        return str(self.value)
