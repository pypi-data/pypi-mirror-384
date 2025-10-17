from enum import Enum


class CatalogFieldResponseDataType(str, Enum):
    CATALOG_FIELDS = "catalog_fields"

    def __str__(self) -> str:
        return str(self.value)
