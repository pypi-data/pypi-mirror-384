from enum import Enum


class OnCallRoleListDataItemType(str, Enum):
    ON_CALL_ROLES = "on_call_roles"

    def __str__(self) -> str:
        return str(self.value)
