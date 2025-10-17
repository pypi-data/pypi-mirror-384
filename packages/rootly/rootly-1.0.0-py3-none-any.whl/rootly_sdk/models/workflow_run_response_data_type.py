from enum import Enum


class WorkflowRunResponseDataType(str, Enum):
    WORKFLOW_RUNS = "workflow_runs"

    def __str__(self) -> str:
        return str(self.value)
