from enum import Enum


class WorkflowTaskResponseDataType(str, Enum):
    WORKFLOW_TASKS = "workflow_tasks"

    def __str__(self) -> str:
        return str(self.value)
