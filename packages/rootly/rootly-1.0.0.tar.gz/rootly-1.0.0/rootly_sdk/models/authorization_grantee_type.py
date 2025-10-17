from enum import Enum


class AuthorizationGranteeType(str, Enum):
    TEAM = "Team"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
