from enum import Enum


class UpdateCatalogFieldDataType(str, Enum):
    CATALOG_FIELDS = "catalog_fields"

    def __str__(self) -> str:
        return str(self.value)
