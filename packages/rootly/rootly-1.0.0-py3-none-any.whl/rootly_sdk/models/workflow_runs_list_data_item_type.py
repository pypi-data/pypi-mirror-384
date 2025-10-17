from enum import Enum


class WorkflowRunsListDataItemType(str, Enum):
    WORKFLOW_RUNS = "workflow_runs"

    def __str__(self) -> str:
        return str(self.value)
