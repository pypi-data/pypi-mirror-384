from enum import Enum


class NewWorkflowTaskDataType(str, Enum):
    WORKFLOW_TASKS = "workflow_tasks"

    def __str__(self) -> str:
        return str(self.value)
