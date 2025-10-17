from typing import Literal, cast

IncidentTriggerParamsIncidentConditionIncidentRoles = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_INCIDENT_ROLES_VALUES: set[
    IncidentTriggerParamsIncidentConditionIncidentRoles
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


def check_incident_trigger_params_incident_condition_incident_roles(
    value: str,
) -> IncidentTriggerParamsIncidentConditionIncidentRoles:
    if value in INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_INCIDENT_ROLES_VALUES:
        return cast(IncidentTriggerParamsIncidentConditionIncidentRoles, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {INCIDENT_TRIGGER_PARAMS_INCIDENT_CONDITION_INCIDENT_ROLES_VALUES!r}"
    )
