from enum import Enum


class UpdateFormFieldDataType(str, Enum):
    FORM_FIELDS = "form_fields"

    def __str__(self) -> str:
        return str(self.value)
