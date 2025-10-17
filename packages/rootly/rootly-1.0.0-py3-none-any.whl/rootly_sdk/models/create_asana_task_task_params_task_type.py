from enum import Enum


class CreateAsanaTaskTaskParamsTaskType(str, Enum):
    CREATE_ASANA_TASK = "create_asana_task"

    def __str__(self) -> str:
        return str(self.value)
