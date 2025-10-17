from enum import Enum


class UpdateOnCallRoleDataAttributesContactsPermissionsItem(str, Enum):
    READ = "read"

    def __str__(self) -> str:
        return str(self.value)
