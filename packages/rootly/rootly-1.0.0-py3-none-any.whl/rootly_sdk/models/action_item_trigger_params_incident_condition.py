from enum import Enum


class ActionItemTriggerParamsIncidentCondition(str, Enum):
    ALL = "ALL"
    ANY = "ANY"
    NONE = "NONE"

    def __str__(self) -> str:
        return str(self.value)
