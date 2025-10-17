from enum import Enum


class NewCauseDataType(str, Enum):
    CAUSES = "causes"

    def __str__(self) -> str:
        return str(self.value)
