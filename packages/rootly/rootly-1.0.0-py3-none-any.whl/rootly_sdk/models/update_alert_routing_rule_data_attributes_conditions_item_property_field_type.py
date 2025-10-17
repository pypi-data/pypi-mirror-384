from enum import Enum


class UpdateAlertRoutingRuleDataAttributesConditionsItemPropertyFieldType(str, Enum):
    ATTRIBUTE = "attribute"
    PAYLOAD = "payload"

    def __str__(self) -> str:
        return str(self.value)
