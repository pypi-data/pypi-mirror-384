from enum import Enum


class UpdateClickupTaskTaskParamsTaskType(str, Enum):
    UPDATE_CLICKUP_TASK = "update_clickup_task"

    def __str__(self) -> str:
        return str(self.value)
