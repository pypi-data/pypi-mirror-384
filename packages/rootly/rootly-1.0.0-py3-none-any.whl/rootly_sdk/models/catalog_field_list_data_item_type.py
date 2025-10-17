from enum import Enum


class CatalogFieldListDataItemType(str, Enum):
    CATALOG_FIELDS = "catalog_fields"

    def __str__(self) -> str:
        return str(self.value)
