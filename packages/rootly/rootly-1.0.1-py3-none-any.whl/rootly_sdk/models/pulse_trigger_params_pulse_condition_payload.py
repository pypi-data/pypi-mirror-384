from typing import Literal, cast

PulseTriggerParamsPulseConditionPayload = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

PULSE_TRIGGER_PARAMS_PULSE_CONDITION_PAYLOAD_VALUES: set[PulseTriggerParamsPulseConditionPayload] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_pulse_trigger_params_pulse_condition_payload(value: str) -> PulseTriggerParamsPulseConditionPayload:
    if value in PULSE_TRIGGER_PARAMS_PULSE_CONDITION_PAYLOAD_VALUES:
        return cast(PulseTriggerParamsPulseConditionPayload, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {PULSE_TRIGGER_PARAMS_PULSE_CONDITION_PAYLOAD_VALUES!r}"
    )
