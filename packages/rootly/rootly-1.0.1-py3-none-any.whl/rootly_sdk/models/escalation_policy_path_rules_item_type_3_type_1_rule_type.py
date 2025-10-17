from typing import Literal, cast

EscalationPolicyPathRulesItemType3Type1RuleType = Literal["working_hour"]

ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_1_RULE_TYPE_VALUES: set[
    EscalationPolicyPathRulesItemType3Type1RuleType
] = {
    "working_hour",
}


def check_escalation_policy_path_rules_item_type_3_type_1_rule_type(
    value: str,
) -> EscalationPolicyPathRulesItemType3Type1RuleType:
    if value in ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_1_RULE_TYPE_VALUES:
        return cast(EscalationPolicyPathRulesItemType3Type1RuleType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_1_RULE_TYPE_VALUES!r}"
    )
