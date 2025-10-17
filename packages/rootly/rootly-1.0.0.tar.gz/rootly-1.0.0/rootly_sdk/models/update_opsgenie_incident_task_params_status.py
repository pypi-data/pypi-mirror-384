from enum import Enum


class UpdateOpsgenieIncidentTaskParamsStatus(str, Enum):
    AUTO = "auto"
    CLOSE = "close"
    OPEN = "open"
    RESOLVE = "resolve"

    def __str__(self) -> str:
        return str(self.value)
