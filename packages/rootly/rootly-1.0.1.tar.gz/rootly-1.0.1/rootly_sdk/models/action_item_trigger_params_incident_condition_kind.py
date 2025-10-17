from typing import Literal, cast

ActionItemTriggerParamsIncidentConditionKind = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

ACTION_ITEM_TRIGGER_PARAMS_INCIDENT_CONDITION_KIND_VALUES: set[ActionItemTriggerParamsIncidentConditionKind] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_action_item_trigger_params_incident_condition_kind(
    value: str,
) -> ActionItemTriggerParamsIncidentConditionKind:
    if value in ACTION_ITEM_TRIGGER_PARAMS_INCIDENT_CONDITION_KIND_VALUES:
        return cast(ActionItemTriggerParamsIncidentConditionKind, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {ACTION_ITEM_TRIGGER_PARAMS_INCIDENT_CONDITION_KIND_VALUES!r}"
    )
