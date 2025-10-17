from enum import Enum


class CustomFormListDataItemType(str, Enum):
    CUSTOM_FORMS = "custom_forms"

    def __str__(self) -> str:
        return str(self.value)
