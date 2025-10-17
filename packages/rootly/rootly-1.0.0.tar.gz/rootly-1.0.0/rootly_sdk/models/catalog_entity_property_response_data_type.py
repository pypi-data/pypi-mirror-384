from enum import Enum


class CatalogEntityPropertyResponseDataType(str, Enum):
    CATALOG_ENTITY_PROPERTIES = "catalog_entity_properties"

    def __str__(self) -> str:
        return str(self.value)
