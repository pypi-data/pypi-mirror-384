from enum import Enum


class AlertEventAction(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    ADDED = "added"
    ANSWERED = "answered"
    ATTACHED = "attached"
    CALLED = "called"
    CREATED = "created"
    EMAILED = "emailed"
    ESCALATED = "escalated"
    ESCALATION_POLICY_PAGED = "escalation_policy_paged"
    MARKED = "marked"
    MUTED = "muted"
    NOTIFIED = "notified"
    NOT_MARKED = "not_marked"
    OPENED = "opened"
    PAGED = "paged"
    REMOVED = "removed"
    RESOLVED = "resolved"
    RETRIGGERED = "retriggered"
    SLACKED = "slacked"
    SNOOZED = "snoozed"
    TEXTED = "texted"
    TRIGGERED = "triggered"
    UPDATED = "updated"

    def __str__(self) -> str:
        return str(self.value)
