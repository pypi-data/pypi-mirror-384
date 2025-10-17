from enum import Enum


class NewEscalationPolicyDataType(str, Enum):
    ESCALATION_POLICIES = "escalation_policies"

    def __str__(self) -> str:
        return str(self.value)
