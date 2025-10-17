from enum import Enum


class IncidentResponseDataType(str, Enum):
    INCIDENTS = "incidents"

    def __str__(self) -> str:
        return str(self.value)
