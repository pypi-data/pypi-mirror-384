from enum import Enum


class FunctionalityListDataItemType(str, Enum):
    FUNCTIONALITIES = "functionalities"

    def __str__(self) -> str:
        return str(self.value)
