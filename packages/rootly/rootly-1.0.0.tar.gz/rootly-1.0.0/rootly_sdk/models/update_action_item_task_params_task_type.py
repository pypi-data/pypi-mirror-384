from enum import Enum


class UpdateActionItemTaskParamsTaskType(str, Enum):
    UPDATE_ACTION_ITEM = "update_action_item"

    def __str__(self) -> str:
        return str(self.value)
