from enum import Enum


class ScheduleRotationActiveDayListDataItemType(str, Enum):
    SCHEDULE_ROTATION_ACTIVE_DAYS = "schedule_rotation_active_days"

    def __str__(self) -> str:
        return str(self.value)
