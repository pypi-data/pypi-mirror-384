from enum import Enum


class GetCatalogEntityInclude(str, Enum):
    CATALOG = "catalog"
    PROPERTIES = "properties"

    def __str__(self) -> str:
        return str(self.value)
