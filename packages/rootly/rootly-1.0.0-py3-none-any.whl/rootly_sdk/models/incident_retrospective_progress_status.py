from enum import Enum


class IncidentRetrospectiveProgressStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    NOT_STARTED = "not_started"
    SKIPPED = "skipped"

    def __str__(self) -> str:
        return str(self.value)
