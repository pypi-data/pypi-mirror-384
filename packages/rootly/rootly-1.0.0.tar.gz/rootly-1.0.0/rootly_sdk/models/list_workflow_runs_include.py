from enum import Enum


class ListWorkflowRunsInclude(str, Enum):
    GENIUS_TASK_RUNS = "genius_task_runs"

    def __str__(self) -> str:
        return str(self.value)
