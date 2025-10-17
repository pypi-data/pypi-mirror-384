from typing import Literal, cast

UpdateAlertDataType = Literal["alerts"]

UPDATE_ALERT_DATA_TYPE_VALUES: set[UpdateAlertDataType] = {
    "alerts",
}


def check_update_alert_data_type(value: str) -> UpdateAlertDataType:
    if value in UPDATE_ALERT_DATA_TYPE_VALUES:
        return cast(UpdateAlertDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_ALERT_DATA_TYPE_VALUES!r}")
