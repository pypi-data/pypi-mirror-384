from enum import Enum


class ListEscalationPathsInclude(str, Enum):
    ESCALATION_POLICY_LEVELS = "escalation_policy_levels"

    def __str__(self) -> str:
        return str(self.value)
