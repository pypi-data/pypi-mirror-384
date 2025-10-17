from enum import Enum


class UpdateAlertsSourceDataType(str, Enum):
    ALERT_SOURCES = "alert_sources"

    def __str__(self) -> str:
        return str(self.value)
