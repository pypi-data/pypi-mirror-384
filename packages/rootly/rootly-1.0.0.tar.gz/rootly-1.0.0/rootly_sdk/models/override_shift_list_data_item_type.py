from enum import Enum


class OverrideShiftListDataItemType(str, Enum):
    SHIFTS = "shifts"

    def __str__(self) -> str:
        return str(self.value)
