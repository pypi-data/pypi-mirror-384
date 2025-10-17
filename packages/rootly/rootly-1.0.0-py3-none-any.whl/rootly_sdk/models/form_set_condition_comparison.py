from enum import Enum


class FormSetConditionComparison(str, Enum):
    EQUAL = "equal"

    def __str__(self) -> str:
        return str(self.value)
