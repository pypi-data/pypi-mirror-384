from enum import Enum


class NewIncidentActionItemDataAttributesKind(str, Enum):
    FOLLOW_UP = "follow_up"
    TASK = "task"

    def __str__(self) -> str:
        return str(self.value)
