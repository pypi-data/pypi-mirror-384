from enum import Enum


class PlaybookTaskResponseDataType(str, Enum):
    PLAYBOOK_TASKS = "playbook_tasks"

    def __str__(self) -> str:
        return str(self.value)
