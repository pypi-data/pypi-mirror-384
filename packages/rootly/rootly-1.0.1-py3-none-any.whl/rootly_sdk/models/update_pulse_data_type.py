from typing import Literal, cast

UpdatePulseDataType = Literal["pulses"]

UPDATE_PULSE_DATA_TYPE_VALUES: set[UpdatePulseDataType] = {
    "pulses",
}


def check_update_pulse_data_type(value: str) -> UpdatePulseDataType:
    if value in UPDATE_PULSE_DATA_TYPE_VALUES:
        return cast(UpdatePulseDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_PULSE_DATA_TYPE_VALUES!r}")
