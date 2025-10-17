from enum import Enum


class UpdateFormFieldPlacementConditionDataType(str, Enum):
    FORM_FIELD_PLACEMENT_CONDITIONS = "form_field_placement_conditions"

    def __str__(self) -> str:
        return str(self.value)
