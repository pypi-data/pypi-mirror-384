from enum import Enum


class GetCustomFieldInclude(str, Enum):
    OPTIONS = "options"

    def __str__(self) -> str:
        return str(self.value)
