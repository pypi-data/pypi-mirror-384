from enum import Enum


class StatusPageTemplateKind(str, Enum):
    NORMAL = "normal"
    SCHEDULED = "scheduled"

    def __str__(self) -> str:
        return str(self.value)
