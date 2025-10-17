from enum import Enum


class UpdateAlertGroupDataAttributesConditionsItemPropertyFieldType(str, Enum):
    ALERT_FIELD = "alert_field"
    ATTRIBUTE = "attribute"
    PAYLOAD = "payload"

    def __str__(self) -> str:
        return str(self.value)
