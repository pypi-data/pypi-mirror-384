from enum import Enum


class GetCatalogFieldInclude(str, Enum):
    CATALOG = "catalog"

    def __str__(self) -> str:
        return str(self.value)
