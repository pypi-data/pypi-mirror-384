from enum import Enum


class IncidentTriggerParamsIncidentConditionSummaryType1(str, Enum):
    SET = "SET"
    UNSET = "UNSET"

    def __str__(self) -> str:
        return str(self.value)
