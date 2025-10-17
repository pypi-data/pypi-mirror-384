from enum import Enum


class UpdateAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemConditionableType(str, Enum):
    ALERTFIELD = "AlertField"

    def __str__(self) -> str:
        return str(self.value)
