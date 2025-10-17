from typing import Literal, cast

PostMortemTriggerParamsIncidentConditionSeverity = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_SEVERITY_VALUES: set[PostMortemTriggerParamsIncidentConditionSeverity] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_post_mortem_trigger_params_incident_condition_severity(
    value: str,
) -> PostMortemTriggerParamsIncidentConditionSeverity:
    if value in POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_SEVERITY_VALUES:
        return cast(PostMortemTriggerParamsIncidentConditionSeverity, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_SEVERITY_VALUES!r}"
    )
