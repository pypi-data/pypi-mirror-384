from enum import Enum


class NewCatalogEntityDataType(str, Enum):
    CATALOG_ENTITIES = "catalog_entities"

    def __str__(self) -> str:
        return str(self.value)
