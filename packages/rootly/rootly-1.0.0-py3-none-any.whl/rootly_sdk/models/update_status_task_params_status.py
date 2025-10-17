from enum import Enum


class UpdateStatusTaskParamsStatus(str, Enum):
    CANCELLED = "cancelled"
    CLOSED = "closed"
    IN_TRIAGE = "in_triage"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    STARTED = "started"

    def __str__(self) -> str:
        return str(self.value)
