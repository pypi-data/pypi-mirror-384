from enum import Enum


class ScheduleListDataItemType(str, Enum):
    SCHEDULES = "schedules"

    def __str__(self) -> str:
        return str(self.value)
