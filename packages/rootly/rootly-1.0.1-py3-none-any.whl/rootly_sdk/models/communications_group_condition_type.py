from typing import Literal, cast

CommunicationsGroupConditionType = Literal["all", "any"]

COMMUNICATIONS_GROUP_CONDITION_TYPE_VALUES: set[CommunicationsGroupConditionType] = {
    "all",
    "any",
}


def check_communications_group_condition_type(value: str) -> CommunicationsGroupConditionType:
    if value in COMMUNICATIONS_GROUP_CONDITION_TYPE_VALUES:
        return cast(CommunicationsGroupConditionType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {COMMUNICATIONS_GROUP_CONDITION_TYPE_VALUES!r}")
