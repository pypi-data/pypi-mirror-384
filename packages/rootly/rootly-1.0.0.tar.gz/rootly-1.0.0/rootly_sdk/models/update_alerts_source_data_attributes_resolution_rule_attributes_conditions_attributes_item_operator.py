from enum import Enum


class UpdateAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemOperator(str, Enum):
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    ENDS_WITH = "ends_with"
    IS = "is"
    IS_NOT = "is_not"
    STARTS_WITH = "starts_with"

    def __str__(self) -> str:
        return str(self.value)
