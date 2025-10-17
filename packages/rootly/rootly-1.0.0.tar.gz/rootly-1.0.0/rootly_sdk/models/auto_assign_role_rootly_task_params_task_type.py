from enum import Enum


class AutoAssignRoleRootlyTaskParamsTaskType(str, Enum):
    AUTO_ASSIGN_ROLE_ROOTLY = "auto_assign_role_rootly"

    def __str__(self) -> str:
        return str(self.value)
