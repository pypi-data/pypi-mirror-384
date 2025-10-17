from enum import Enum


class UpdateCatalogFieldDataAttributesKind(str, Enum):
    REFERENCE = "reference"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)
