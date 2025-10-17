from enum import Enum


class CustomFieldOptionResponseDataType(str, Enum):
    CUSTOM_FIELD_OPTIONS = "custom_field_options"

    def __str__(self) -> str:
        return str(self.value)
