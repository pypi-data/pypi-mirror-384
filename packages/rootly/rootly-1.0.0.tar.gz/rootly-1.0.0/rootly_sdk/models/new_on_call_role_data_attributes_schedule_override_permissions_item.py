from enum import Enum


class NewOnCallRoleDataAttributesScheduleOverridePermissionsItem(str, Enum):
    CREATE = "create"
    UPDATE = "update"

    def __str__(self) -> str:
        return str(self.value)
