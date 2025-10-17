from enum import Enum


class UpdateFormSetConditionDataAttributesComparison(str, Enum):
    EQUAL = "equal"

    def __str__(self) -> str:
        return str(self.value)
