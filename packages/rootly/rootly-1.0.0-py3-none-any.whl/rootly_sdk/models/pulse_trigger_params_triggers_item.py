from enum import Enum


class PulseTriggerParamsTriggersItem(str, Enum):
    PULSE_CREATED = "pulse_created"

    def __str__(self) -> str:
        return str(self.value)
