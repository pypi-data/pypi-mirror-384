from enum import Enum


class NewPulseDataType(str, Enum):
    PULSES = "pulses"

    def __str__(self) -> str:
        return str(self.value)
