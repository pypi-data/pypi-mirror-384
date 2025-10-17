from typing import Literal, cast

IncidentTriggerParamsIncidentConditionService = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_SERVICE_VALUES: set[IncidentTriggerParamsIncidentConditionService] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_incident_trigger_params_incident_condition_service(
    value: str,
) -> IncidentTriggerParamsIncidentConditionService:
    if value in INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_SERVICE_VALUES:
        return cast(IncidentTriggerParamsIncidentConditionService, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_SERVICE_VALUES!r}"
    )
