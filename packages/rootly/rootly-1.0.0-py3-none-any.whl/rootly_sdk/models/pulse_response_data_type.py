from enum import Enum


class PulseResponseDataType(str, Enum):
    PULSES = "pulses"

    def __str__(self) -> str:
        return str(self.value)
