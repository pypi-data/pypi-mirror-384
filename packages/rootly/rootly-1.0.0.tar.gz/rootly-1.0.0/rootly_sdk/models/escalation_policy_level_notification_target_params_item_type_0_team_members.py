from enum import Enum


class EscalationPolicyLevelNotificationTargetParamsItemType0TeamMembers(str, Enum):
    ADMINS = "admins"
    ALL = "all"
    ESCALATE = "escalate"

    def __str__(self) -> str:
        return str(self.value)
