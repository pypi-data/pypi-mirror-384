from typing import Literal, cast

AlertStatus = Literal["acknowledged", "open", "resolved", "triggered"]

ALERT_STATUS_VALUES: set[AlertStatus] = {
    "acknowledged",
    "open",
    "resolved",
    "triggered",
}


def check_alert_status(value: str) -> AlertStatus:
    if value in ALERT_STATUS_VALUES:
        return cast(AlertStatus, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ALERT_STATUS_VALUES!r}")
