from typing import Literal, cast

UpdateScheduleRotationDataType = Literal["schedule_rotations"]

UPDATE_SCHEDULE_ROTATION_DATA_TYPE_VALUES: set[UpdateScheduleRotationDataType] = {
    "schedule_rotations",
}


def check_update_schedule_rotation_data_type(value: str) -> UpdateScheduleRotationDataType:
    if value in UPDATE_SCHEDULE_ROTATION_DATA_TYPE_VALUES:
        return cast(UpdateScheduleRotationDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_SCHEDULE_ROTATION_DATA_TYPE_VALUES!r}")
