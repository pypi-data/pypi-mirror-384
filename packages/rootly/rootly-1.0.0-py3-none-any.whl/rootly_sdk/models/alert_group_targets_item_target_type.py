from enum import Enum


class AlertGroupTargetsItemTargetType(str, Enum):
    ESCALATIONPOLICY = "EscalationPolicy"
    GROUP = "Group"
    SERVICE = "Service"

    def __str__(self) -> str:
        return str(self.value)
