from enum import Enum


class AddActionItemTaskParamsTaskType(str, Enum):
    ADD_ACTION_ITEM = "add_action_item"

    def __str__(self) -> str:
        return str(self.value)
