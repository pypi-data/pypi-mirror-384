from typing import Literal, cast

IncidentTriggerParamsIncidentConditionFunctionality = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_FUNCTIONALITY_VALUES: set[
    IncidentTriggerParamsIncidentConditionFunctionality
] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_incident_trigger_params_incident_condition_functionality(
    value: str,
) -> IncidentTriggerParamsIncidentConditionFunctionality:
    if value in INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_FUNCTIONALITY_VALUES:
        return cast(IncidentTriggerParamsIncidentConditionFunctionality, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_FUNCTIONALITY_VALUES!r}"
    )
