from enum import Enum


class NewHeartbeatDataAttributesIntervalUnit(str, Enum):
    HOURS = "hours"
    MINUTES = "minutes"
    SECONDS = "seconds"

    def __str__(self) -> str:
        return str(self.value)
