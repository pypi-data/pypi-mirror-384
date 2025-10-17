from enum import Enum


class EscalationPolicyListDataItemType(str, Enum):
    ESCALATION_POLICIES = "escalation_policies"

    def __str__(self) -> str:
        return str(self.value)
