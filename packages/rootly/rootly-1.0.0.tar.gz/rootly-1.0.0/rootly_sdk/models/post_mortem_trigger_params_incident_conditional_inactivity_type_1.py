from enum import Enum


class PostMortemTriggerParamsIncidentConditionalInactivityType1(str, Enum):
    IS = "IS"

    def __str__(self) -> str:
        return str(self.value)
