from enum import Enum


class ListShiftsInclude(str, Enum):
    SHIFT_OVERRIDE = "shift_override"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
