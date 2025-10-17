from typing import Literal, cast

NewScheduleRotationDataAttributesScheduleRotationableType = Literal[
    "ScheduleBiweeklyRotation",
    "ScheduleCustomRotation",
    "ScheduleDailyRotation",
    "ScheduleMonthlyRotation",
    "ScheduleWeeklyRotation",
]

NEW_SCHEDULE_ROTATION_DATA_ATTRIBUTES_SCHEDULE_ROTATIONABLE_TYPE_VALUES: set[
    NewScheduleRotationDataAttributesScheduleRotationableType
] = {
    "ScheduleBiweeklyRotation",
    "ScheduleCustomRotation",
    "ScheduleDailyRotation",
    "ScheduleMonthlyRotation",
    "ScheduleWeeklyRotation",
}


def check_new_schedule_rotation_data_attributes_schedule_rotationable_type(
    value: str,
) -> NewScheduleRotationDataAttributesScheduleRotationableType:
    if value in NEW_SCHEDULE_ROTATION_DATA_ATTRIBUTES_SCHEDULE_ROTATIONABLE_TYPE_VALUES:
        return cast(NewScheduleRotationDataAttributesScheduleRotationableType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {NEW_SCHEDULE_ROTATION_DATA_ATTRIBUTES_SCHEDULE_ROTATIONABLE_TYPE_VALUES!r}"
    )
