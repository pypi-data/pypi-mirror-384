from enum import Enum


class ShiftOverrideResponseDataType(str, Enum):
    SHIFT_OVERRIDE = "shift_override"

    def __str__(self) -> str:
        return str(self.value)
