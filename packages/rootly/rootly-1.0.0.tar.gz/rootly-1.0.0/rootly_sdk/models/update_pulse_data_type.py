from enum import Enum


class UpdatePulseDataType(str, Enum):
    PULSES = "pulses"

    def __str__(self) -> str:
        return str(self.value)
