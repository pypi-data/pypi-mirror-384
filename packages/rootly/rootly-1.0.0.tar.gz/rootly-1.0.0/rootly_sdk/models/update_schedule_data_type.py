from enum import Enum


class UpdateScheduleDataType(str, Enum):
    SCHEDULES = "schedules"

    def __str__(self) -> str:
        return str(self.value)
