from enum import Enum


class UpdateCauseDataType(str, Enum):
    CAUSES = "causes"

    def __str__(self) -> str:
        return str(self.value)
