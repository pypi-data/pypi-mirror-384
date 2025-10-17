from enum import Enum


class UpdateStatusTaskParamsTaskType(str, Enum):
    UPDATE_STATUS = "update_status"

    def __str__(self) -> str:
        return str(self.value)
