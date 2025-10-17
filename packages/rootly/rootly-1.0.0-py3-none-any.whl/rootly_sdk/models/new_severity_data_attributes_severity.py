from enum import Enum


class NewSeverityDataAttributesSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    LOW = "low"
    MEDIUM = "medium"

    def __str__(self) -> str:
        return str(self.value)
