from enum import Enum


class ListCatalogFieldsInclude(str, Enum):
    CATALOG = "catalog"

    def __str__(self) -> str:
        return str(self.value)
