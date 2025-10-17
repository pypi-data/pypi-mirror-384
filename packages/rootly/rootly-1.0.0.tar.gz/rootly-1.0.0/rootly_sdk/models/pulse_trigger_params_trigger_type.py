from enum import Enum


class PulseTriggerParamsTriggerType(str, Enum):
    PULSE = "pulse"

    def __str__(self) -> str:
        return str(self.value)
