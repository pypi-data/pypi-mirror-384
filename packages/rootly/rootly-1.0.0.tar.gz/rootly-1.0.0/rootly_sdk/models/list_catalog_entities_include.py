from enum import Enum


class ListCatalogEntitiesInclude(str, Enum):
    CATALOG = "catalog"
    PROPERTIES = "properties"

    def __str__(self) -> str:
        return str(self.value)
