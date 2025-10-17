from enum import Enum


class CreateShortcutTaskTaskParamsTaskType(str, Enum):
    CREATE_SHORTCUT_TASK = "create_shortcut_task"

    def __str__(self) -> str:
        return str(self.value)
