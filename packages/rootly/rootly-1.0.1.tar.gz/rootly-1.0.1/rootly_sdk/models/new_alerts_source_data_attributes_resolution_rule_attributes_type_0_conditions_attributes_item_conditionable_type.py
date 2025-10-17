from typing import Literal, cast

NewAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemConditionableType = Literal[
    "AlertField"
]

NEW_ALERTS_SOURCE_DATA_ATTRIBUTES_RESOLUTION_RULE_ATTRIBUTES_TYPE_0_CONDITIONS_ATTRIBUTES_ITEM_CONDITIONABLE_TYPE_VALUES: set[
    NewAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemConditionableType
] = {
    "AlertField",
}


def check_new_alerts_source_data_attributes_resolution_rule_attributes_type_0_conditions_attributes_item_conditionable_type(
    value: str,
) -> NewAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemConditionableType:
    if (
        value
        in NEW_ALERTS_SOURCE_DATA_ATTRIBUTES_RESOLUTION_RULE_ATTRIBUTES_TYPE_0_CONDITIONS_ATTRIBUTES_ITEM_CONDITIONABLE_TYPE_VALUES
    ):
        return cast(
            NewAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemConditionableType, value
        )
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {NEW_ALERTS_SOURCE_DATA_ATTRIBUTES_RESOLUTION_RULE_ATTRIBUTES_TYPE_0_CONDITIONS_ATTRIBUTES_ITEM_CONDITIONABLE_TYPE_VALUES!r}"
    )
