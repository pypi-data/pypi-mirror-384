from enum import Enum


class EscalationPolicyPathResponseDataType(str, Enum):
    ESCALATION_PATHS = "escalation_paths"

    def __str__(self) -> str:
        return str(self.value)
