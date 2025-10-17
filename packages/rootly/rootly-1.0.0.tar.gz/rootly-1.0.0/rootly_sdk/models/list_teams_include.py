from enum import Enum


class ListTeamsInclude(str, Enum):
    USERS = "users"

    def __str__(self) -> str:
        return str(self.value)
