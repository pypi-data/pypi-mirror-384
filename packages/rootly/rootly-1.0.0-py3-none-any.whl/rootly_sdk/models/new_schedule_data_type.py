from enum import Enum


class NewScheduleDataType(str, Enum):
    SCHEDULES = "schedules"

    def __str__(self) -> str:
        return str(self.value)
