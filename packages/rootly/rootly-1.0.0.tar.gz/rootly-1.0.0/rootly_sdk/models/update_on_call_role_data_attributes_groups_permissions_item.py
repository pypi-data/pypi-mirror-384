from enum import Enum


class UpdateOnCallRoleDataAttributesGroupsPermissionsItem(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    READ = "read"
    UPDATE = "update"

    def __str__(self) -> str:
        return str(self.value)
