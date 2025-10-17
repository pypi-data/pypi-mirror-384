from enum import Enum


class NewCommunicationsTypeDataType(str, Enum):
    COMMUNICATIONS_TYPES = "communications_types"

    def __str__(self) -> str:
        return str(self.value)
