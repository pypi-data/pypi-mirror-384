from enum import Enum


class UpdateStatusPageTemplateDataAttributesKind(str, Enum):
    NORMAL = "normal"
    SCHEDULED = "scheduled"

    def __str__(self) -> str:
        return str(self.value)
