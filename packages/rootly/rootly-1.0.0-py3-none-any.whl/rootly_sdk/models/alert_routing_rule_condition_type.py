from enum import Enum


class AlertRoutingRuleConditionType(str, Enum):
    ALL = "all"
    ANY = "any"

    def __str__(self) -> str:
        return str(self.value)
