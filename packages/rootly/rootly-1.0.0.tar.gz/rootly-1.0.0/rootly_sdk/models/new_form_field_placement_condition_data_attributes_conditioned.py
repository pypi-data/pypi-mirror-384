from enum import Enum


class NewFormFieldPlacementConditionDataAttributesConditioned(str, Enum):
    PLACEMENT = "placement"
    REQUIRED = "required"

    def __str__(self) -> str:
        return str(self.value)
