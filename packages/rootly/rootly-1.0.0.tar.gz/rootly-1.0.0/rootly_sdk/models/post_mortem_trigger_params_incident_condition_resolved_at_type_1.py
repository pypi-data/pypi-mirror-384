from enum import Enum


class PostMortemTriggerParamsIncidentConditionResolvedAtType1(str, Enum):
    SET = "SET"
    UNSET = "UNSET"

    def __str__(self) -> str:
        return str(self.value)
