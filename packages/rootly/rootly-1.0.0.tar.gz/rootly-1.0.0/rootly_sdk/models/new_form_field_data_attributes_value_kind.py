from enum import Enum


class NewFormFieldDataAttributesValueKind(str, Enum):
    CATALOG_ENTITY = "catalog_entity"
    FUNCTIONALITY = "functionality"
    GROUP = "group"
    INHERIT = "inherit"
    SERVICE = "service"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
