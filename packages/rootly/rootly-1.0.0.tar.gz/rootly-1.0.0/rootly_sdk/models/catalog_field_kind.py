from enum import Enum


class CatalogFieldKind(str, Enum):
    REFERENCE = "reference"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)
