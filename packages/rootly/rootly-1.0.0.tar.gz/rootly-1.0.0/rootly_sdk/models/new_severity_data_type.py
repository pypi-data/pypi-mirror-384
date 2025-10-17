from enum import Enum


class NewSeverityDataType(str, Enum):
    SEVERITIES = "severities"

    def __str__(self) -> str:
        return str(self.value)
