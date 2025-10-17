from typing import Literal, cast

UpdateAlertDataAttributesNoise = Literal["noise", "not_noise"]

UPDATE_ALERT_DATA_ATTRIBUTES_NOISE_VALUES: set[UpdateAlertDataAttributesNoise] = {
    "noise",
    "not_noise",
}


def check_update_alert_data_attributes_noise(value: str) -> UpdateAlertDataAttributesNoise:
    if value in UPDATE_ALERT_DATA_ATTRIBUTES_NOISE_VALUES:
        return cast(UpdateAlertDataAttributesNoise, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_ALERT_DATA_ATTRIBUTES_NOISE_VALUES!r}")
