from enum import Enum


class NewPlaybookDataType(str, Enum):
    PLAYBOOKS = "playbooks"

    def __str__(self) -> str:
        return str(self.value)
