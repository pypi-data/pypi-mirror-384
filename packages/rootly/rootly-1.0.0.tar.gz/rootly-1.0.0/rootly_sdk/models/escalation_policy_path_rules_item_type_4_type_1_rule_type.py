from enum import Enum


class EscalationPolicyPathRulesItemType4Type1RuleType(str, Enum):
    WORKING_HOUR = "working_hour"

    def __str__(self) -> str:
        return str(self.value)
