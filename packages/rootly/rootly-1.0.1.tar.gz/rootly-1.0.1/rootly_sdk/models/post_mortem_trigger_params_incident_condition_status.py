from typing import Literal, cast

PostMortemTriggerParamsIncidentConditionStatus = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_STATUS_VALUES: set[PostMortemTriggerParamsIncidentConditionStatus] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_post_mortem_trigger_params_incident_condition_status(
    value: str,
) -> PostMortemTriggerParamsIncidentConditionStatus:
    if value in POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_STATUS_VALUES:
        return cast(PostMortemTriggerParamsIncidentConditionStatus, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_STATUS_VALUES!r}"
    )
