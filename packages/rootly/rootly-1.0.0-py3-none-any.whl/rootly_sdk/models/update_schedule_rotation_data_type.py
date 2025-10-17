from enum import Enum


class UpdateScheduleRotationDataType(str, Enum):
    SCHEDULE_ROTATIONS = "schedule_rotations"

    def __str__(self) -> str:
        return str(self.value)
