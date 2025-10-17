from enum import Enum


class IncidentTriggerParamsIncidentStatusesItem(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    CANCELLED = "cancelled"
    CLOSED = "closed"
    COMPLETED = "completed"
    DETECTED = "detected"
    IN_PROGRESS = "in_progress"
    IN_TRIAGE = "in_triage"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    SCHEDULED = "scheduled"
    STARTED = "started"

    def __str__(self) -> str:
        return str(self.value)
