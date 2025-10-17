from typing import Literal, cast

ScheduleResponseDataType = Literal["schedules"]

SCHEDULE_RESPONSE_DATA_TYPE_VALUES: set[ScheduleResponseDataType] = {
    "schedules",
}


def check_schedule_response_data_type(value: str) -> ScheduleResponseDataType:
    if value in SCHEDULE_RESPONSE_DATA_TYPE_VALUES:
        return cast(ScheduleResponseDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {SCHEDULE_RESPONSE_DATA_TYPE_VALUES!r}")
