from enum import Enum


class UpdateCatalogEntityPropertyDataType(str, Enum):
    CATALOG_ENTITY_PROPERTIES = "catalog_entity_properties"

    def __str__(self) -> str:
        return str(self.value)
