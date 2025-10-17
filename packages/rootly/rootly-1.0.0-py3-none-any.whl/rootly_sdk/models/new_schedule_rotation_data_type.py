from enum import Enum


class NewScheduleRotationDataType(str, Enum):
    SCHEDULE_ROTATIONS = "schedule_rotations"

    def __str__(self) -> str:
        return str(self.value)
