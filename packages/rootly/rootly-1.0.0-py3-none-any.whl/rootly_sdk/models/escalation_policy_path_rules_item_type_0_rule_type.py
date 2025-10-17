from enum import Enum


class EscalationPolicyPathRulesItemType0RuleType(str, Enum):
    ALERT_URGENCY = "alert_urgency"

    def __str__(self) -> str:
        return str(self.value)
