from enum import Enum


class UpdateAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemKind(str, Enum):
    ALERT_FIELD = "alert_field"
    PAYLOAD = "payload"

    def __str__(self) -> str:
        return str(self.value)
