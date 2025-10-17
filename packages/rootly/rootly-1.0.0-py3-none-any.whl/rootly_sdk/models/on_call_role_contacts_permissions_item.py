from enum import Enum


class OnCallRoleContactsPermissionsItem(str, Enum):
    READ = "read"

    def __str__(self) -> str:
        return str(self.value)
