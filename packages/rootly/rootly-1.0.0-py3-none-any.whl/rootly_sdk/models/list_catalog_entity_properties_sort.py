from enum import Enum


class ListCatalogEntityPropertiesSort(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    VALUE_1 = "-created_at"
    VALUE_3 = "-updated_at"

    def __str__(self) -> str:
        return str(self.value)
