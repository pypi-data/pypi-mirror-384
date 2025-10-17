from enum import Enum


class ActionItemTriggerParamsTriggerType(str, Enum):
    ACTION_ITEM = "action_item"

    def __str__(self) -> str:
        return str(self.value)
