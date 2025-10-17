from enum import Enum


class NewRoleDataType(str, Enum):
    ROLES = "roles"

    def __str__(self) -> str:
        return str(self.value)
