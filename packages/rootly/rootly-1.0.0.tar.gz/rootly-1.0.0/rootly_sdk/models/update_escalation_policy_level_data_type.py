from enum import Enum


class UpdateEscalationPolicyLevelDataType(str, Enum):
    ESCALATION_LEVELS = "escalation_levels"

    def __str__(self) -> str:
        return str(self.value)
