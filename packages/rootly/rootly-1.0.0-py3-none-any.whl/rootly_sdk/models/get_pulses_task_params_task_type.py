from enum import Enum


class GetPulsesTaskParamsTaskType(str, Enum):
    GET_PULSES = "get_pulses"

    def __str__(self) -> str:
        return str(self.value)
