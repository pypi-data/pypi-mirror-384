from enum import Enum


class NewAlertEventDataAttributesKind(str, Enum):
    NOTE = "note"

    def __str__(self) -> str:
        return str(self.value)
