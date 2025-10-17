from enum import Enum


class AutoAssignRoleVictorOpsTaskParamsTaskType(str, Enum):
    AUTO_ASSIGN_ROLE_VICTOR_OPS = "auto_assign_role_victor_ops"

    def __str__(self) -> str:
        return str(self.value)
