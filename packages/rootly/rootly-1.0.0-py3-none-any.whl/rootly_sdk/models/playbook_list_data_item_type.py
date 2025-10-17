from enum import Enum


class PlaybookListDataItemType(str, Enum):
    PLAYBOOKS = "playbooks"

    def __str__(self) -> str:
        return str(self.value)
