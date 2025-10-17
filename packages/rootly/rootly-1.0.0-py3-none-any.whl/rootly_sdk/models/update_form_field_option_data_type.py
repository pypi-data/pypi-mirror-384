from enum import Enum


class UpdateFormFieldOptionDataType(str, Enum):
    FORM_FIELD_OPTIONS = "form_field_options"

    def __str__(self) -> str:
        return str(self.value)
