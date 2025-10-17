from enum import Enum


class UpdatePagertreeAlertTaskParamsUrgency(str, Enum):
    AUTO = "auto"
    CRITICAL = "critical"
    HIGH = "high"
    LOW = "low"
    MEDIUM = "medium"

    def __str__(self) -> str:
        return str(self.value)
