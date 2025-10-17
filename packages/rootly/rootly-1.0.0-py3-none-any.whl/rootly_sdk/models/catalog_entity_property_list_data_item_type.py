from enum import Enum


class CatalogEntityPropertyListDataItemType(str, Enum):
    CATALOG_ENTITY_PROPERTIES = "catalog_entity_properties"

    def __str__(self) -> str:
        return str(self.value)
