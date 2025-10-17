from enum import Enum


class WorkflowRunStatus(str, Enum):
    CANCELED = "canceled"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    QUEUED = "queued"
    STARTED = "started"

    def __str__(self) -> str:
        return str(self.value)
