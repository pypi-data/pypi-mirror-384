from enum import Enum


class AutoAssignRoleOpsgenieTaskParamsTaskType(str, Enum):
    AUTO_ASSIGN_ROLE_OPSGENIE = "auto_assign_role_opsgenie"

    def __str__(self) -> str:
        return str(self.value)
