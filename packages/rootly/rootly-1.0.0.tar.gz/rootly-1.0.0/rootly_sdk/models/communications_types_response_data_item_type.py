from enum import Enum


class CommunicationsTypesResponseDataItemType(str, Enum):
    COMMUNICATIONS_TYPES = "communications_types"

    def __str__(self) -> str:
        return str(self.value)
