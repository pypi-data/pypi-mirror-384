from enum import Enum


class EscalationPolicyResponseDataType(str, Enum):
    ESCALATION_POLICIES = "escalation_policies"

    def __str__(self) -> str:
        return str(self.value)
