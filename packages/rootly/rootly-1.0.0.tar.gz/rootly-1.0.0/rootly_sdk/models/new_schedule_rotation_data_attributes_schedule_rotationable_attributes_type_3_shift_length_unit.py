from enum import Enum


class NewScheduleRotationDataAttributesScheduleRotationableAttributesType3ShiftLengthUnit(str, Enum):
    DAYS = "days"
    HOURS = "hours"
    WEEKS = "weeks"

    def __str__(self) -> str:
        return str(self.value)
