from enum import Enum


class UpdateCatalogDataType(str, Enum):
    CATALOGS = "catalogs"

    def __str__(self) -> str:
        return str(self.value)
