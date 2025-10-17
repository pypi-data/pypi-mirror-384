from enum import Enum


class FormFieldPositionResponseDataType(str, Enum):
    FORM_FIELD_POSITIONS = "form_field_positions"

    def __str__(self) -> str:
        return str(self.value)
