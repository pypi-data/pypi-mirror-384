from enum import Enum


class SimpleTriggerParamsTriggerType(str, Enum):
    SIMPLE = "simple"

    def __str__(self) -> str:
        return str(self.value)
