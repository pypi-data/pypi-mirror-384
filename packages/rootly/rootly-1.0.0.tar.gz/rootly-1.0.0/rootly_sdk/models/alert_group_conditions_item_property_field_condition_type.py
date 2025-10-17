from enum import Enum


class AlertGroupConditionsItemPropertyFieldConditionType(str, Enum):
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    ENDS_WITH = "ends_with"
    IS_EMPTY = "is_empty"
    IS_NOT_ONE_OF = "is_not_one_of"
    IS_ONE_OF = "is_one_of"
    MATCHES_EXISTING_ALERT = "matches_existing_alert"
    MATCHES_REGEX = "matches_regex"
    STARTS_WITH = "starts_with"

    def __str__(self) -> str:
        return str(self.value)
