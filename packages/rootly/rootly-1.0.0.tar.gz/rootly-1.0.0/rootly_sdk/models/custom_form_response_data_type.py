from enum import Enum


class CustomFormResponseDataType(str, Enum):
    CUSTOM_FORMS = "custom_forms"

    def __str__(self) -> str:
        return str(self.value)
