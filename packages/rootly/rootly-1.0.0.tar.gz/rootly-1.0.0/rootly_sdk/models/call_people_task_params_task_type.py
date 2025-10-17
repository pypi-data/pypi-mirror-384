from enum import Enum


class CallPeopleTaskParamsTaskType(str, Enum):
    CALL_PEOPLE = "call_people"

    def __str__(self) -> str:
        return str(self.value)
