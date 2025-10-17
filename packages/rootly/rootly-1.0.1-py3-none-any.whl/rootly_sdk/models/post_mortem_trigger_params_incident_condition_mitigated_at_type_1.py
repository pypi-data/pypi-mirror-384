from typing import Literal, cast

PostMortemTriggerParamsIncidentConditionMitigatedAtType1 = Literal["SET", "UNSET"]

POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_MITIGATED_AT_TYPE_1_VALUES: set[
    PostMortemTriggerParamsIncidentConditionMitigatedAtType1
] = {
    "SET",
    "UNSET",
}


def check_post_mortem_trigger_params_incident_condition_mitigated_at_type_1(
    value: str,
) -> PostMortemTriggerParamsIncidentConditionMitigatedAtType1:
    if value in POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_MITIGATED_AT_TYPE_1_VALUES:
        return cast(PostMortemTriggerParamsIncidentConditionMitigatedAtType1, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {POST_MORTEM_TRIGGER_PARAMS_INCIDENT_CONDITION_MITIGATED_AT_TYPE_1_VALUES!r}"
    )
