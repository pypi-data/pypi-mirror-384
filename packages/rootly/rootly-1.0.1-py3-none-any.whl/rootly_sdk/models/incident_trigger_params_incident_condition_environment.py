from typing import Literal, cast

IncidentTriggerParamsIncidentConditionEnvironment = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_ENVIRONMENT_VALUES: set[
    IncidentTriggerParamsIncidentConditionEnvironment
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


def check_incident_trigger_params_incident_condition_environment(
    value: str,
) -> IncidentTriggerParamsIncidentConditionEnvironment:
    if value in INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_ENVIRONMENT_VALUES:
        return cast(IncidentTriggerParamsIncidentConditionEnvironment, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_ENVIRONMENT_VALUES!r}"
    )
