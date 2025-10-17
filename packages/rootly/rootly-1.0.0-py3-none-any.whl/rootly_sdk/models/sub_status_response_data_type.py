from enum import Enum


class SubStatusResponseDataType(str, Enum):
    SUB_STATUSES = "sub_statuses"

    def __str__(self) -> str:
        return str(self.value)
