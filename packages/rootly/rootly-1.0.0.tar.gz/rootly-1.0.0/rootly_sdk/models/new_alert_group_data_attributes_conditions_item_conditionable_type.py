from enum import Enum


class NewAlertGroupDataAttributesConditionsItemConditionableType(str, Enum):
    ALERTFIELD = "AlertField"

    def __str__(self) -> str:
        return str(self.value)
