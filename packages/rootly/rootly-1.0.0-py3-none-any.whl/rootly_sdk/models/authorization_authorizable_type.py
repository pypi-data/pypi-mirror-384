from enum import Enum


class AuthorizationAuthorizableType(str, Enum):
    DASHBOARD = "Dashboard"

    def __str__(self) -> str:
        return str(self.value)
