from enum import Enum


class IncidentRetrospectiveStepStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    SKIPPED = "skipped"
    TODO = "todo"

    def __str__(self) -> str:
        return str(self.value)
