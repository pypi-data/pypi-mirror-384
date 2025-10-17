from enum import Enum


class IncidentTriggerParamsIncidentConditionalInactivityType1(str, Enum):
    IS = "IS"

    def __str__(self) -> str:
        return str(self.value)
