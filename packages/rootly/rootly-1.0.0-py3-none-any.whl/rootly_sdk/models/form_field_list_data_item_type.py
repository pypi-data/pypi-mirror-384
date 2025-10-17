from enum import Enum


class FormFieldListDataItemType(str, Enum):
    FORM_FIELDS = "form_fields"

    def __str__(self) -> str:
        return str(self.value)
