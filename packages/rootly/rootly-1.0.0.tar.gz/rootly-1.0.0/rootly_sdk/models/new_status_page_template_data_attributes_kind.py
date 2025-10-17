from enum import Enum


class NewStatusPageTemplateDataAttributesKind(str, Enum):
    NORMAL = "normal"
    SCHEDULED = "scheduled"

    def __str__(self) -> str:
        return str(self.value)
