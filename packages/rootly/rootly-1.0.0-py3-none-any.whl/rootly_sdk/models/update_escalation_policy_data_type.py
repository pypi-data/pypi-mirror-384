from enum import Enum


class UpdateEscalationPolicyDataType(str, Enum):
    ESCALATION_POLICIES = "escalation_policies"

    def __str__(self) -> str:
        return str(self.value)
