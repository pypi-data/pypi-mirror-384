from enum import Enum


class NewFunctionalityDataType(str, Enum):
    FUNCTIONALITIES = "functionalities"

    def __str__(self) -> str:
        return str(self.value)
