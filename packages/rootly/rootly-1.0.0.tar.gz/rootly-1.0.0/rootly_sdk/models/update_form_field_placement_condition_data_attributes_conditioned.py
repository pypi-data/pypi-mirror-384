from enum import Enum


class UpdateFormFieldPlacementConditionDataAttributesConditioned(str, Enum):
    PLACEMENT = "placement"
    REQUIRED = "required"

    def __str__(self) -> str:
        return str(self.value)
