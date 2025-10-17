from enum import Enum


class NewFormSetConditionDataAttributesComparison(str, Enum):
    EQUAL = "equal"

    def __str__(self) -> str:
        return str(self.value)
