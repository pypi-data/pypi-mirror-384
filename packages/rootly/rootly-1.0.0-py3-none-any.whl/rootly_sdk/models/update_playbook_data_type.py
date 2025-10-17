from enum import Enum


class UpdatePlaybookDataType(str, Enum):
    PLAYBOOKS = "playbooks"

    def __str__(self) -> str:
        return str(self.value)
