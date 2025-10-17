from enum import Enum


class GetEscalationPathInclude(str, Enum):
    ESCALATION_POLICY_LEVELS = "escalation_policy_levels"

    def __str__(self) -> str:
        return str(self.value)
