from enum import Enum


class RoleResponseDataType(str, Enum):
    ROLES = "roles"

    def __str__(self) -> str:
        return str(self.value)
