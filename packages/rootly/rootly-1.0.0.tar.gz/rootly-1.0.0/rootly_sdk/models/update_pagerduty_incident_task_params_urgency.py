from enum import Enum


class UpdatePagerdutyIncidentTaskParamsUrgency(str, Enum):
    AUTO = "auto"
    HIGH = "high"
    LOW = "low"

    def __str__(self) -> str:
        return str(self.value)
