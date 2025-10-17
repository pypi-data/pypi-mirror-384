from enum import Enum


class ScheduleRotationScheduleRotationableAttributesType2HandoffDay(str, Enum):
    FIRST_DAY_OF_MONTH = "first_day_of_month"
    LAST_DAY_OF_MONTH = "last_day_of_month"

    def __str__(self) -> str:
        return str(self.value)
