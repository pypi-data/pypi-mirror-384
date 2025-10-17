from enum import Enum


class UpdateRetrospectiveProcessDataType(str, Enum):
    RETROSPECTIVE_PROCESSES = "retrospective_processes"

    def __str__(self) -> str:
        return str(self.value)
