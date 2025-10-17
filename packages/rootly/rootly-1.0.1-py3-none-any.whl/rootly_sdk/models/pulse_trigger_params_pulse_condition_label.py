from typing import Literal, cast

PulseTriggerParamsPulseConditionLabel = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

PULSE_TRIGGER_PARAMS_PULSE_CONDITION_LABEL_VALUES: set[PulseTriggerParamsPulseConditionLabel] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_pulse_trigger_params_pulse_condition_label(value: str) -> PulseTriggerParamsPulseConditionLabel:
    if value in PULSE_TRIGGER_PARAMS_PULSE_CONDITION_LABEL_VALUES:
        return cast(PulseTriggerParamsPulseConditionLabel, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {PULSE_TRIGGER_PARAMS_PULSE_CONDITION_LABEL_VALUES!r}"
    )
