from enum import Enum


class NewCatalogDataType(str, Enum):
    CATALOGS = "catalogs"

    def __str__(self) -> str:
        return str(self.value)
