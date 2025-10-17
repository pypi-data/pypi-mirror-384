from enum import Enum


class EscalationPolicyLevelResponseDataType(str, Enum):
    ESCALATION_LEVELS = "escalation_levels"

    def __str__(self) -> str:
        return str(self.value)
