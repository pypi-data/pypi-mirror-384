from enum import Enum


class ScheduleResponseDataType(str, Enum):
    SCHEDULES = "schedules"

    def __str__(self) -> str:
        return str(self.value)
