from enum import Enum


class EscalationPolicyPathMatchMode(str, Enum):
    MATCH_ALL_RULES = "match-all-rules"
    MATCH_ANY_RULE = "match-any-rule"

    def __str__(self) -> str:
        return str(self.value)
