from enum import Enum


class SubStatusParentStatus(str, Enum):
    CANCELLED = "cancelled"
    CLOSED = "closed"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    IN_TRIAGE = "in_triage"
    RESOLVED = "resolved"
    SCHEDULED = "scheduled"
    STARTED = "started"

    def __str__(self) -> str:
        return str(self.value)
