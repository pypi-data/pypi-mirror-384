from enum import Enum


class UpdateShortcutStoryTaskParamsTaskType(str, Enum):
    UPDATE_SHORTCUT_STORY = "update_shortcut_story"

    def __str__(self) -> str:
        return str(self.value)
