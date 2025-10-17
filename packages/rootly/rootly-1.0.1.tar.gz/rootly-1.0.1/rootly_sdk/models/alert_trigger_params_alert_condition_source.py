from typing import Literal, cast

AlertTriggerParamsAlertConditionSource = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

ALERT_TRIGGER_PARAMS_ALERT_CONDITION_SOURCE_VALUES: set[AlertTriggerParamsAlertConditionSource] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_alert_trigger_params_alert_condition_source(value: str) -> AlertTriggerParamsAlertConditionSource:
    if value in ALERT_TRIGGER_PARAMS_ALERT_CONDITION_SOURCE_VALUES:
        return cast(AlertTriggerParamsAlertConditionSource, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {ALERT_TRIGGER_PARAMS_ALERT_CONDITION_SOURCE_VALUES!r}"
    )
