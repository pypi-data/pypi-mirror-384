from enum import Enum


class NewOverrideShiftDataType(str, Enum):
    SHIFTS = "shifts"

    def __str__(self) -> str:
        return str(self.value)
