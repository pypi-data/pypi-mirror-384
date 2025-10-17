from enum import Enum


class EscalationPolicyPathRulesItemType3Type0RuleType(str, Enum):
    ALERT_URGENCY = "alert_urgency"

    def __str__(self) -> str:
        return str(self.value)
