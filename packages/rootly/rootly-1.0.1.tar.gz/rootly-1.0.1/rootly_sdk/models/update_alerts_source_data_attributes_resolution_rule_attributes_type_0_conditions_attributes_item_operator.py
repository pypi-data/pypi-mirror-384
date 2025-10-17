from typing import Literal, cast

UpdateAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemOperator = Literal[
    "contains", "does_not_contain", "ends_with", "is", "is_not", "starts_with"
]

UPDATE_ALERTS_SOURCE_DATA_ATTRIBUTES_RESOLUTION_RULE_ATTRIBUTES_TYPE_0_CONDITIONS_ATTRIBUTES_ITEM_OPERATOR_VALUES: set[
    UpdateAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemOperator
] = {
    "contains",
    "does_not_contain",
    "ends_with",
    "is",
    "is_not",
    "starts_with",
}


def check_update_alerts_source_data_attributes_resolution_rule_attributes_type_0_conditions_attributes_item_operator(
    value: str,
) -> UpdateAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemOperator:
    if (
        value
        in UPDATE_ALERTS_SOURCE_DATA_ATTRIBUTES_RESOLUTION_RULE_ATTRIBUTES_TYPE_0_CONDITIONS_ATTRIBUTES_ITEM_OPERATOR_VALUES
    ):
        return cast(
            UpdateAlertsSourceDataAttributesResolutionRuleAttributesType0ConditionsAttributesItemOperator, value
        )
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_ALERTS_SOURCE_DATA_ATTRIBUTES_RESOLUTION_RULE_ATTRIBUTES_TYPE_0_CONDITIONS_ATTRIBUTES_ITEM_OPERATOR_VALUES!r}"
    )
