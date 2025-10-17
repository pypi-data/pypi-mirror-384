from enum import Enum


class NewPlaybookTaskDataType(str, Enum):
    PLAYBOOK_TASKS = "playbook_tasks"

    def __str__(self) -> str:
        return str(self.value)
