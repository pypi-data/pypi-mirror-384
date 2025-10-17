from enum import Enum


class ActionItemTriggerParamsIncidentActionItemKindsItem(str, Enum):
    FOLLOW_UP = "follow_up"
    TASK = "task"

    def __str__(self) -> str:
        return str(self.value)
