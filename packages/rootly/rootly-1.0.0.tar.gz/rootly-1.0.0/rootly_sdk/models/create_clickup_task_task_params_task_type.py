from enum import Enum


class CreateClickupTaskTaskParamsTaskType(str, Enum):
    CREATE_CLICKUP_TASK = "create_clickup_task"

    def __str__(self) -> str:
        return str(self.value)
