from enum import Enum


class PostMortemTriggerParamsIncidentPostMortemCondition(str, Enum):
    ALL = "ALL"
    ANY = "ANY"
    NONE = "NONE"

    def __str__(self) -> str:
        return str(self.value)
