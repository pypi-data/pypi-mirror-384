from enum import Enum


class UpdatePagerdutyIncidentTaskParamsStatus(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    AUTO = "auto"
    RESOLVED = "resolved"

    def __str__(self) -> str:
        return str(self.value)
