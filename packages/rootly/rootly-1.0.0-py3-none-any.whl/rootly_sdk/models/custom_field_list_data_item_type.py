from enum import Enum


class CustomFieldListDataItemType(str, Enum):
    CUSTOM_FIELDS = "custom_fields"

    def __str__(self) -> str:
        return str(self.value)
