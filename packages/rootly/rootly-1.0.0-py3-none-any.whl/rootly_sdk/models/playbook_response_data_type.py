from enum import Enum


class PlaybookResponseDataType(str, Enum):
    PLAYBOOKS = "playbooks"

    def __str__(self) -> str:
        return str(self.value)
