from enum import Enum


class UpdateFormFieldPlacementDataType(str, Enum):
    FORM_FIELD_PLACEMENTS = "form_field_placements"

    def __str__(self) -> str:
        return str(self.value)
