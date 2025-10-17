from enum import Enum


class RoleAlertsPermissionsItem(str, Enum):
    CREATE = "create"
    READ = "read"

    def __str__(self) -> str:
        return str(self.value)
