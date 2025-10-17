from typing import Literal, cast

IncidentTriggerParamsIncidentConditionalInactivityType1 = Literal["IS"]

INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITIONAL_INACTIVITY_TYPE_1_VALUES: set[
    IncidentTriggerParamsIncidentConditionalInactivityType1
] = {
    "IS",
}


def check_incident_trigger_params_incident_conditional_inactivity_type_1(
    value: str,
) -> IncidentTriggerParamsIncidentConditionalInactivityType1:
    if value in INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITIONAL_INACTIVITY_TYPE_1_VALUES:
        return cast(IncidentTriggerParamsIncidentConditionalInactivityType1, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITIONAL_INACTIVITY_TYPE_1_VALUES!r}"
    )
