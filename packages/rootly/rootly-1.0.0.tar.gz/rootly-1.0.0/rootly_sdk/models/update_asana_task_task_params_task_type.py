from enum import Enum


class UpdateAsanaTaskTaskParamsTaskType(str, Enum):
    UPDATE_ASANA_TASK = "update_asana_task"

    def __str__(self) -> str:
        return str(self.value)
