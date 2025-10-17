from enum import Enum


class UpdateOverrideShiftDataType(str, Enum):
    SHIFTS = "shifts"

    def __str__(self) -> str:
        return str(self.value)
