from enum import Enum


class CommunicationsGroupsResponseDataItemType(str, Enum):
    COMMUNICATIONS_GROUPS = "communications-groups"

    def __str__(self) -> str:
        return str(self.value)
