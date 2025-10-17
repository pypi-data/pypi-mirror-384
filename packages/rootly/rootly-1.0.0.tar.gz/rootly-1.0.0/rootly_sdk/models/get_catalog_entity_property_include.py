from enum import Enum


class GetCatalogEntityPropertyInclude(str, Enum):
    CATALOG_ENTITY = "catalog_entity"
    CATALOG_FIELD = "catalog_field"

    def __str__(self) -> str:
        return str(self.value)
