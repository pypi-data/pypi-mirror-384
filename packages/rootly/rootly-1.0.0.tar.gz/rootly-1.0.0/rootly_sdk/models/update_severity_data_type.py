from enum import Enum


class UpdateSeverityDataType(str, Enum):
    SEVERITIES = "severities"

    def __str__(self) -> str:
        return str(self.value)
