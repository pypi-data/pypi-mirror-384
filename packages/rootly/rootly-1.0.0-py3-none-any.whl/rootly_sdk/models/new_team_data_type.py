from enum import Enum


class NewTeamDataType(str, Enum):
    GROUPS = "groups"

    def __str__(self) -> str:
        return str(self.value)
