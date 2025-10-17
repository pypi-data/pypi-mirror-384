from enum import Enum


class IncidentTriggerParamsIncidentConditionDetectedAtType1(str, Enum):
    SET = "SET"
    UNSET = "UNSET"

    def __str__(self) -> str:
        return str(self.value)
