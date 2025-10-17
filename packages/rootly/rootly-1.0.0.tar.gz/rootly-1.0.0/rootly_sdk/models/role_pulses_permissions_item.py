from enum import Enum


class RolePulsesPermissionsItem(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"

    def __str__(self) -> str:
        return str(self.value)
