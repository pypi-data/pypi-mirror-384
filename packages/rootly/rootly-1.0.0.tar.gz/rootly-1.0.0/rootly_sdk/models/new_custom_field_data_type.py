from enum import Enum


class NewCustomFieldDataType(str, Enum):
    CUSTOM_FIELDS = "custom_fields"

    def __str__(self) -> str:
        return str(self.value)
