from enum import Enum


class OnCallRoleAlertsPermissionsItem(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"

    def __str__(self) -> str:
        return str(self.value)
