from typing import Literal, cast

EscalationPolicyPathRulesItemType3Type0RuleType = Literal["alert_urgency"]

ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_0_RULE_TYPE_VALUES: set[
    EscalationPolicyPathRulesItemType3Type0RuleType
] = {
    "alert_urgency",
}


def check_escalation_policy_path_rules_item_type_3_type_0_rule_type(
    value: str,
) -> EscalationPolicyPathRulesItemType3Type0RuleType:
    if value in ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_0_RULE_TYPE_VALUES:
        return cast(EscalationPolicyPathRulesItemType3Type0RuleType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {ESCALATION_POLICY_PATH_RULES_ITEM_TYPE_3_TYPE_0_RULE_TYPE_VALUES!r}"
    )
