from typing import Literal, cast

EscalationPolicyPathRulesItemType3Type2Operator = Literal["contains", "does_not_contain", "is", "is_not"]

ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_2_OPERATOR_VALUES: set[
    EscalationPolicyPathRulesItemType3Type2Operator
] = {
    "contains",
    "does_not_contain",
    "is",
    "is_not",
}


def check_escalation_policy_path_rules_item_type_3_type_2_operator(
    value: str,
) -> EscalationPolicyPathRulesItemType3Type2Operator:
    if value in ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_2_OPERATOR_VALUES:
        return cast(EscalationPolicyPathRulesItemType3Type2Operator, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_2_OPERATOR_VALUES!r}"
    )
