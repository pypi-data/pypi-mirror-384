from enum import Enum


class UpdateAlertsSourceDataAttributesResolutionRuleAttributesIdentifierMatchableType(str, Enum):
    ALERTFIELD = "AlertField"

    def __str__(self) -> str:
        return str(self.value)
