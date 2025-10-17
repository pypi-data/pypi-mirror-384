from enum import Enum


class ListCustomFieldsInclude(str, Enum):
    OPTIONS = "options"

    def __str__(self) -> str:
        return str(self.value)
