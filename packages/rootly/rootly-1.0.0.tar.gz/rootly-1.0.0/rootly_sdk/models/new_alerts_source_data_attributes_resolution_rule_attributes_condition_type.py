from enum import Enum


class NewAlertsSourceDataAttributesResolutionRuleAttributesConditionType(str, Enum):
    ALL = "all"
    ANY = "any"

    def __str__(self) -> str:
        return str(self.value)
