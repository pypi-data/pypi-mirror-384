from enum import Enum


class UpdateAlertGroupDataAttributesConditionsItemConditionableType(str, Enum):
    ALERTFIELD = "AlertField"

    def __str__(self) -> str:
        return str(self.value)
