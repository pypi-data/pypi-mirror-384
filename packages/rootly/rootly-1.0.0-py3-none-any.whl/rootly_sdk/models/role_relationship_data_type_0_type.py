from enum import Enum


class RoleRelationshipDataType0Type(str, Enum):
    ROLES = "roles"

    def __str__(self) -> str:
        return str(self.value)
