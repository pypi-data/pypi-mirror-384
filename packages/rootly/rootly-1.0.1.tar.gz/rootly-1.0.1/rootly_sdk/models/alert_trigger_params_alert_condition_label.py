from typing import Literal, cast

AlertTriggerParamsAlertConditionLabel = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

ALERT_TRIGGER_PARAMS_ALERT_CONDITION_LABEL_VALUES: set[AlertTriggerParamsAlertConditionLabel] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_alert_trigger_params_alert_condition_label(value: str) -> AlertTriggerParamsAlertConditionLabel:
    if value in ALERT_TRIGGER_PARAMS_ALERT_CONDITION_LABEL_VALUES:
        return cast(AlertTriggerParamsAlertConditionLabel, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {ALERT_TRIGGER_PARAMS_ALERT_CONDITION_LABEL_VALUES!r}"
    )
