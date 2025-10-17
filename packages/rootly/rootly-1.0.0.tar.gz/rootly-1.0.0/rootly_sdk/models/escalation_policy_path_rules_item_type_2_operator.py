from enum import Enum


class EscalationPolicyPathRulesItemType2Operator(str, Enum):
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    IS = "is"
    IS_NOT = "is_not"

    def __str__(self) -> str:
        return str(self.value)
