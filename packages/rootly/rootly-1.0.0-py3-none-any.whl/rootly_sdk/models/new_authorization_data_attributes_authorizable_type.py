from enum import Enum


class NewAuthorizationDataAttributesAuthorizableType(str, Enum):
    DASHBOARD = "Dashboard"

    def __str__(self) -> str:
        return str(self.value)
