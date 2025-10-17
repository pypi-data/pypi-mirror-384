from enum import Enum


class CreateAsanaSubtaskTaskParamsTaskType(str, Enum):
    CREATE_ASANA_SUBTASK = "create_asana_subtask"

    def __str__(self) -> str:
        return str(self.value)
