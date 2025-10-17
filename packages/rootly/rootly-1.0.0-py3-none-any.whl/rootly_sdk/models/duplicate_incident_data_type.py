from enum import Enum


class DuplicateIncidentDataType(str, Enum):
    INCIDENTS = "incidents"

    def __str__(self) -> str:
        return str(self.value)
