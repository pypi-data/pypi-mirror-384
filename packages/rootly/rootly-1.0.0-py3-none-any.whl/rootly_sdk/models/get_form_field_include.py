from enum import Enum


class GetFormFieldInclude(str, Enum):
    OPTIONS = "options"
    POSITIONS = "positions"

    def __str__(self) -> str:
        return str(self.value)
