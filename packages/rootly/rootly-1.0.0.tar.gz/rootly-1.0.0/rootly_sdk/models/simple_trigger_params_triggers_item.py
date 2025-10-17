from enum import Enum


class SimpleTriggerParamsTriggersItem(str, Enum):
    SLACK_COMMAND = "slack_command"

    def __str__(self) -> str:
        return str(self.value)
