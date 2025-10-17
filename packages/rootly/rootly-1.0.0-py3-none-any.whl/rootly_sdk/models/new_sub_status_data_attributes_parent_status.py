from enum import Enum


class NewSubStatusDataAttributesParentStatus(str, Enum):
    RETROSPECTIVE = "retrospective"
    STARTED = "started"

    def __str__(self) -> str:
        return str(self.value)
