from enum import Enum


class ScheduleRotationScheduleRotationableAttributesType3ShiftLengthUnit(str, Enum):
    DAYS = "days"
    HOURS = "hours"
    WEEKS = "weeks"

    def __str__(self) -> str:
        return str(self.value)
