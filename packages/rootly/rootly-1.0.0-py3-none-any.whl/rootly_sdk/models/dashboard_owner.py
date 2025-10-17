from enum import Enum


class DashboardOwner(str, Enum):
    TEAM = "team"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
