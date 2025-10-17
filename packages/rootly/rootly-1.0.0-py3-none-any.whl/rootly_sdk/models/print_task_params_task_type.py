from enum import Enum


class PrintTaskParamsTaskType(str, Enum):
    PRINT = "print"

    def __str__(self) -> str:
        return str(self.value)
