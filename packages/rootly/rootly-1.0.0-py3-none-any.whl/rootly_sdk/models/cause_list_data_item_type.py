from enum import Enum


class CauseListDataItemType(str, Enum):
    CAUSES = "causes"

    def __str__(self) -> str:
        return str(self.value)
