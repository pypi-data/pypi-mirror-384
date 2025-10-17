from enum import Enum


class UpdateShortcutTaskTaskParamsTaskType(str, Enum):
    UPDATE_SHORTCUT_TASK = "update_shortcut_task"

    def __str__(self) -> str:
        return str(self.value)
