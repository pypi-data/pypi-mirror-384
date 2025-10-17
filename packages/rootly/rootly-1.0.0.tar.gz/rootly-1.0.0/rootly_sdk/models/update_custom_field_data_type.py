from enum import Enum


class UpdateCustomFieldDataType(str, Enum):
    CUSTOM_FIELDS = "custom_fields"

    def __str__(self) -> str:
        return str(self.value)
