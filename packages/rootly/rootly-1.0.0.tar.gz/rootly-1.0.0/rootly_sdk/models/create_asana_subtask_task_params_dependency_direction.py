from enum import Enum


class CreateAsanaSubtaskTaskParamsDependencyDirection(str, Enum):
    BLOCKED_BY = "blocked_by"
    BLOCKING = "blocking"

    def __str__(self) -> str:
        return str(self.value)
