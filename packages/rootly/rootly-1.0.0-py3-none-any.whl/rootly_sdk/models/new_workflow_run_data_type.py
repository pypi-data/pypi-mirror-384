from enum import Enum


class NewWorkflowRunDataType(str, Enum):
    WORKFLOW_RUNS = "workflow_runs"

    def __str__(self) -> str:
        return str(self.value)
