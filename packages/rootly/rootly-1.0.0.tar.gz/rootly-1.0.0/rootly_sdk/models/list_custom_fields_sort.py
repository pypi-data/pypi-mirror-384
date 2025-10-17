from enum import Enum


class ListCustomFieldsSort(str, Enum):
    CREATED_AT = "created_at"
    POSITION = "position"
    UPDATED_AT = "updated_at"
    VALUE_1 = "-created_at"
    VALUE_3 = "-updated_at"
    VALUE_5 = "-position"

    def __str__(self) -> str:
        return str(self.value)
