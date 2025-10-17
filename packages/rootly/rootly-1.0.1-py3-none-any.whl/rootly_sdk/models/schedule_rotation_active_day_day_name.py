from typing import Literal, cast

ScheduleRotationActiveDayDayName = Literal["F", "M", "R", "S", "T", "U", "W"]

SCHEDULE_ROTATION_ACTIVE_DAY_DAY_NAME_VALUES: set[ScheduleRotationActiveDayDayName] = {
    "F",
    "M",
    "R",
    "S",
    "T",
    "U",
    "W",
}


def check_schedule_rotation_active_day_day_name(value: str) -> ScheduleRotationActiveDayDayName:
    if value in SCHEDULE_ROTATION_ACTIVE_DAY_DAY_NAME_VALUES:
        return cast(ScheduleRotationActiveDayDayName, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {SCHEDULE_ROTATION_ACTIVE_DAY_DAY_NAME_VALUES!r}")
