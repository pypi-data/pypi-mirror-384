from enum import Enum


class CancelIncidentDataType(str, Enum):
    INCIDENTS = "incidents"

    def __str__(self) -> str:
        return str(self.value)
