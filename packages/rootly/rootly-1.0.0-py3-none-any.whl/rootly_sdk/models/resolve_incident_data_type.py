from enum import Enum


class ResolveIncidentDataType(str, Enum):
    INCIDENTS = "incidents"

    def __str__(self) -> str:
        return str(self.value)
