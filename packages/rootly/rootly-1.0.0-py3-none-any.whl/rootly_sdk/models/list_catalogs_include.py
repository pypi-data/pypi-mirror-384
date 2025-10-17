from enum import Enum


class ListCatalogsInclude(str, Enum):
    ENTITIES = "entities"
    FIELDS = "fields"

    def __str__(self) -> str:
        return str(self.value)
