from enum import Enum


class NewAlertsSourceDataAttributesResolutionRuleAttributesIdentifierMatchableType(str, Enum):
    ALERTFIELD = "AlertField"

    def __str__(self) -> str:
        return str(self.value)
