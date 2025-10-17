from enum import Enum


class IncidentTriggerParamsIncidentConditionService(str, Enum):
    ANY = "ANY"
    CONTAINS = "CONTAINS"
    CONTAINS_ALL = "CONTAINS_ALL"
    CONTAINS_NONE = "CONTAINS_NONE"
    IS = "IS"
    NONE = "NONE"
    SET = "SET"
    UNSET = "UNSET"

    def __str__(self) -> str:
        return str(self.value)
