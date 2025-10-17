from enum import Enum


class NewOnCallRoleDataAttributesContactsPermissionsItem(str, Enum):
    READ = "read"

    def __str__(self) -> str:
        return str(self.value)
